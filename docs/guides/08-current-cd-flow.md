# 現状の GitHub Actions CD フロー

このドキュメントは、**今この repo で実際に動いている本番デプロイの流れ**を説明するためのものです。  
構築方法や導入経緯ではなく、`git push` から本番アプリ確認までの処理を、初心者向けに時系列で整理しています。

---

## 最初に押さえること

- 現状の GitHub Actions は、**CI より CD が中心**です。
- つまり「テストを自動実行して品質確認する仕組み」よりも、「本番へ自動デプロイする仕組み」が先に入っています。
- 対象ワークフローは **[`.github/workflows/deploy.yml`](../../.github/workflows/deploy.yml)** の 1 本です。
- このワークフローの役割は、以下を自動でつなぐことです。
  - GitHub Actions で Docker イメージを作る
  - AWS ECR に push する
  - AWS Systems Manager で EC2 にデプロイ命令を送る
  - 本番アプリのヘルスチェックを行う

---

## CD 全体像

```text
main に push
  -> GitHub Actions 起動
  -> AWS に OIDC 認証
  -> Docker イメージを build
  -> ECR に push
  -> SSM Run Command で EC2 にデプロイ
  -> migrate 実行
  -> django コンテナ再起動
  -> コンテナ health check
  -> ALB 経由で /diary/health/ を確認
```

---

## 1. ワークフローが起動する条件

- `main` ブランチに `push` されると起動します。
- ただし、次の変更だけなら起動しません。
  - `docs/**`
  - ルート直下の `*.md`
  - `terraform/**`
- GitHub の Actions タブから **手動実行** する `workflow_dispatch` も有効です。
- つまり現状は、**アプリ本体の変更が main に入ると本番デプロイが走る**構成です。

---

## 2. GitHub Actions 側で最初に行うこと

### 2-1. 実行マシンを用意する

- GitHub が `ubuntu-latest` の runner を起動します。
- ジョブ名は `build-and-deploy` です。
- 実行対象の Environment は `production` です。

### 2-2. ソースコードを取得する

- `actions/checkout@v4` で repo の中身を runner に取得します。
- ここで Dockerfile や Django アプリのコードが、GitHub Actions 上で使える状態になります。

### 2-3. AWS に認証する

- `aws-actions/configure-aws-credentials@v4` で AWS 認証を行います。
- 認証方式は **OIDC** です。
- GitHub Secrets に保存された `AWS_ROLE_ARN` を使って、GitHub Actions が AWS IAM Role を引き受けます。
- これにより、固定の Access Key を GitHub に置かずに AWS を操作できます。
- リージョンは `ap-northeast-1` です。

### 2-4. ECR にログインする

- `aws-actions/amazon-ecr-login@v2` で Amazon ECR にログインします。
- ここで取得した ECR のレジストリ URL は、後で Docker イメージの push と EC2 デプロイに使われます。

### 2-5. Docker Buildx を準備する

- `docker/setup-buildx-action@v3` で Buildx を有効にします。
- 目的は、Docker ビルドのキャッシュを効かせてビルドを安定・高速化することです。

---

## 3. Docker イメージを build して ECR に push する流れ

### 3-1. 本番用 Dockerfile を使って build する

- `docker/build-push-action@v6` が実行されます。
- 使用する Dockerfile は **[`compose/production/django/Dockerfile`](../../compose/production/django/Dockerfile)** です。
- この Dockerfile では次のような処理を行います。
  - Python 依存関係を `uv` でインストール
  - アプリコードをコピー
  - 翻訳ファイルを `compilemessages`
  - 静的ファイルを `collectstatic`

### 3-2. イメージにタグを付ける

- build したイメージには 2 つのタグを付けます。
  - `${github.sha}`
  - `latest`
- `${github.sha}` は、そのコミット固有のバージョンです。
- `latest` は「いまの最新イメージ」を指すためのタグです。

### 3-3. ECR に push する

- ECR リポジトリ `school-diary-production-django` にイメージを push します。
- GitHub Actions のキャッシュ `gha` を使っているので、毎回すべてをゼロから build するわけではありません。

---

## 4. AWS 側でデプロイする流れ

### 4-1. GitHub Actions から EC2 に直接 SSH はしない

- 現状は SSH ではなく、**AWS Systems Manager の SSM Run Command** を使います。
- GitHub Actions は AWS API を通じて、EC2 にシェルコマンドを送ります。
- 対象の EC2 は GitHub Secrets の `EC2_INSTANCE_ID` で指定されます。

### 4-2. SSM で送っているコマンドの流れ

- 以前は、`deploy.yml` に長いコマンド列を直接書いていました。
- 改善後は、GitHub Actions が **[`scripts/ssm-deploy.sh`](../../scripts/ssm-deploy.sh)** を EC2 に渡して実行します。
- これにより、処理の見通しとログの追いやすさを改善しています。
- EC2 側では次の順番で処理が進みます。
  - `set -Eeuo pipefail` で、想定外の失敗を早めに検知する
  - `/opt/app` に移動する
  - 今動いている Django コンテナのイメージ名を表示する
  - 今回デプロイするイメージタグを表示する
  - `aws ecr get-login-password` で EC2 側の Docker を ECR にログインさせる
  - `docker compose -f docker-compose.production.yml pull django` を実行する
  - `docker compose -f docker-compose.production.yml run --rm django python manage.py migrate --noinput` を実行する
  - `docker compose -f docker-compose.production.yml up -d django` を実行する
  - `docker compose ps` とコンテナログを表示する
  - 一定回数のループで、コンテナが `healthy` になるまで待つ
  - healthy にならなければ `latest` タグで簡易ロールバックする
  - 最後に不要な Docker イメージを `docker image prune -f` で削除する

### 4-3. pull のとき、どのイメージを取ってくるのか

- **[`docker-compose.production.yml`](../../docker-compose.production.yml)** では、django サービスの `image` が次の形です。

```yaml
image: ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG:-latest}
```

- つまり SSM で設定した `IMAGE_TAG=${github.sha}` が、そのまま今回のデプロイ対象になります。
- そのため EC2 は、GitHub Actions で build 済みのコミット SHA イメージを pull します。

### 4-4. migrate はどのタイミングで走るか

- 新しいイメージを pull したあと、`up -d` の前に `python manage.py migrate --noinput` を実行します。
- つまり、**アプリを新しく起動する前に DB スキーマを更新する**流れです。

### 4-5. django コンテナ起動時に何が起こるか

- django コンテナは `command: /start` で起動します。
- ただし、その前に entrypoint として **[`compose/production/django/entrypoint`](../../compose/production/django/entrypoint)** が実行されます。
- entrypoint では次を行います。
  - `DATABASE_URL` を組み立てる
  - PostgreSQL が起動するまで待つ
  - `collectstatic --noinput` を実行する
- その後、**[`compose/production/django/start`](../../compose/production/django/start)** が Gunicorn を起動します。

### 4-6. コンテナ health check を確認する

- `docker-compose.production.yml` には django サービスの `healthcheck` があります。
- 実行コマンドは `python manage.py check --deploy` です。
- 改善後の SSM スクリプトは、`docker inspect` で health status を一定回数確認します。
- そのため、短時間の起動待ちですぐ失敗扱いにするのではなく、コンテナが安定するまで少し待てます。
- `healthy` になれば、その時点で「コンテナ起動は成功」と判断します。

### 4-7. コンテナが healthy にならないとき

- SSM スクリプトは `Health check failed, rolling back` を表示します。
- その後 `IMAGE_TAG=latest` に切り替えて、再度 `docker compose ... up -d django` を実行します。
- これは**簡易ロールバック**です。
- 厳密に「1 つ前に成功したコミット SHA へ戻す」方式ではなく、`latest` タグに依存しています。

---

## 5. GitHub Actions は EC2 の結果を待つ

- GitHub Actions は SSM コマンドを送って終わりではありません。
- `aws ssm get-command-invocation` を使って、EC2 側の処理状態を 10 秒ごとに確認します。
- 改善後は最大 180 回確認するので、待機時間は最大 30 分です。
- 状態ごとの動きは次の通りです。
  - `Success`: デプロイ成功として次へ進む
  - `Failed`、`Cancelled`、`TimedOut`、`ExecutionTimedOut` など: ワークフローを失敗にする
  - 30 分を超えた場合: タイムアウトとして失敗にする
- また、成功時・失敗時・タイムアウト時のどれでも、SSM の `StandardOutputContent` と `StandardErrorContent` を GitHub Actions のログに表示します。
- これにより「EC2 側のどの処理で止まったか」を追いやすくなります。

---

## 6. 最後の疎通確認

### 6-1. ALB の DNS 名を取得する

- `aws elbv2 describe-load-balancers` を使って、`school-diary-production-alb` の DNS 名を取得します。
- DNS 名が取得できないときは、警告を出してこの確認ステップは終了します。
- 取得できた場合は、確認に使う ALB DNS をログに表示します。

### 6-2. アプリの health URL を HTTP で確認する

- 確認先 URL は次です。

```text
http://<ALB_DNS>/diary/health/
```

- GitHub Actions は `curl` で HTTP ステータスを確認します。
- 10 秒ごとに最大 6 回試行します。
- 1 回でも `200` が返れば、デプロイ成功としてワークフロー完了です。
- 最後まで `200` が返らなければ、最後に取得した HTTP ステータスを表示して失敗になります。

---

## 7. 関連する設定ファイルと役割

- **[`.github/workflows/deploy.yml`](../../.github/workflows/deploy.yml)**
  - GitHub Actions の本体です。
  - トリガー、AWS 認証、Docker build/push、SSM デプロイ、最終確認までを定義しています。
- **[`scripts/ssm-deploy.sh`](../../scripts/ssm-deploy.sh)**
  - EC2 上で実行するデプロイ手順の正本です。
  - 各フェーズのログ出力、health check 待機、簡易ロールバックを持ちます。
- **[`docker-compose.production.yml`](../../docker-compose.production.yml)**
  - EC2 上で django コンテナをどう起動するかを定義しています。
  - どの ECR イメージを pull するか、どの health check を使うかもここで決まります。
- **[`compose/production/django/Dockerfile`](../../compose/production/django/Dockerfile)**
  - 本番用アプリイメージを build する設計書です。
  - 依存関係の導入や `collectstatic` など、イメージ作成時の処理を持ちます。
- **[`terraform/modules/github_actions/main.tf`](../../terraform/modules/github_actions/main.tf)**
  - GitHub Actions が AWS に入るための OIDC Provider と IAM Role を作る Terraform 定義です。
  - ECR への push 権限と、SSM で EC2 にコマンド送信する権限もここで付与しています。

---

## 8. 現状の制約と注意点

- 現状は **CI ワークフロー未整備**です。
  - 自動テストや lint を通してから本番へ出す構成にはなっていません。
- `main` への push が、そのまま本番デプロイの起点になります。
  - ブランチ保護や PR 必須運用が弱いと、誤反映のリスクがあります。
- ロールバックは `latest` を使った簡易方式です。
  - 「直前の成功版に厳密に戻す」仕組みではありません。
- デプロイ先は単一 EC2 前提です。
  - Auto Scaling や複数台切り替えを前提にした構成ではありません。

---

## 9. 失敗時にどこを見るか

- まず GitHub Actions の `Deploy to EC2 via SSM` ステップで、`SSM Command ID` を確認します。
- 次に、そのステップの末尾に出る以下を確認します。
  - `SSM Standard Output`
  - `SSM Standard Error`
- ここで確認できる代表例は次です。
  - ECR login で止まった
  - `pull django` で止まった
  - `migrate` で止まった
  - コンテナが `healthy` にならずロールバックした
- GitHub Actions のログだけで足りなければ、AWS Systems Manager の Run Command 履歴から同じ `Command ID` を開くと、EC2 側の詳細ログを追えます。

---

## 参考

- 構築方法と導入経緯: [GitHub Actions CI/CD の構築](./06-github-actions-cicd.md)
- 改善テーマとしての位置づけ: [GitHub Actions デプロイパイプライン](../improvements/cicd-pipeline.md)
