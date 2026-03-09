# 現状の GitHub Actions CD フロー

このドキュメントは、**今この repo で実際に動いている本番デプロイの流れ**を説明するためのものです。  
構築方法や導入経緯ではなく、`git push` から本番アプリ確認までの処理を、初心者向けに時系列で整理しています。

---

## 最初に押さえること

- 現状の GitHub Actions は、**CI より CD が中心**です。
- つまり「テストを自動実行して品質確認する仕組み」よりも、「本番へ自動デプロイする仕組み」が先に入っています。
- 対象ワークフローは **[`.github/workflows/deploy.yml`](../../.github/workflows/deploy.yml)** の 1 本です。
- この repo の責務分担は次で固定しています。
  - Terraform: インフラと設定の正本
  - SSM: 本番設定の保管庫
  - EC2: 実行主体
  - GitHub Actions: オーケストレーター
- このワークフローの役割は、以下を自動でつなぐことです。
  - GitHub Actions で Docker イメージを作る
  - AWS ECR に push する
  - AWS Systems Manager で EC2 上の固定 deploy script を実行する
  - 本番アプリのヘルスチェックを行う

---

## CD 全体像

```text
production-config apply
  -> SSM に永続設定 / secret を保存
  -> production apply
  -> AWS リソース作成 + 動的 SSM 値を更新
  -> EC2 user_data bootstrap
  -> EC2 が GitHub から bootstrap ファイルを取得
  -> EC2 が SSM から .env を生成
  -> GitHub Actions 手動実行または push
main に push
  -> GitHub Actions 起動
  -> AWS に OIDC 認証
  -> Docker イメージを build
  -> ECR に push
  -> EC2 で GitHub から deploy 用ファイルを同期
  -> EC2 で SSM Parameter Store から .env を再生成
  -> SSM Run Command で EC2 の deploy script を実行
  -> migrate 実行
  -> django コンテナ再起動
  -> コンテナ health check
  -> ALB 経由で /diary/health/ を確認
```

この workflow が成功する前提:

- `production-config` が先に apply されている
- `production` が apply され、動的 SSM 値が更新済みである
- EC2 bootstrap が完了している
- GitHub Secrets に `AWS_ROLE_ARN` と `EC2_INSTANCE_ID` が入っている

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

- GitHub Actions は deploy の実行主体ではなく、EC2 に「今回の deploy を始める」指示を出す役割です。
- 実際の本番反映は、EC2 上の **[`scripts/ssm-deploy.sh`](../../scripts/ssm-deploy.sh)** が担います。
- EC2 側では次の順番で処理が進みます。
  - `/opt/app/bin/sync-app-files.sh` で GitHub から `docker-compose.production.yml` と deploy script 群を取得する
  - `/opt/app/bin/render-env-from-ssm.sh` で SSM Parameter Store から `.envs/.production/*` を生成する
  - `/opt/app/bin/ssm-deploy.sh` を実行する
  - deploy script の中で ECR login、pull、migrate、up -d、health check、rollback、cleanup を行う

補足:

- 永続設定と secret は `terraform/environments/production-config` が管理する
- ALB DNS / CloudFront / RDS endpoint のような再生成値は `terraform/environments/production` が SSM を更新する
- そのため、`terraform destroy` を繰り返す運用でも secret を毎回入れ直さずに済む
- EC2 bootstrap が最初に取る Git ref は `terraform/environments/production` の `github_bootstrap_ref` で、当面 `main` を前提にする

### 4-2.1 bootstrap が先にやっていること

GitHub Actions の deploy が始まる前に、EC2 の `user_data` は次を実行している。

- GitHub raw から `scripts/bootstrap/sync-app-files.sh` を取得する
- `sync-app-files.sh` が `docker-compose.production.yml` / `ssm-deploy.sh` / `render-env-from-ssm.sh` を取得する
- `render-env-from-ssm.sh` が `DJANGO_SECRET_KEY` と動的 SSM 値を読んで `.envs/.production/*` を生成する

つまり、GitHub Actions の成否は workflow 単体ではなく、先に完了している bootstrap と SSM の状態にも依存する。
逆に言うと、bootstrap の補助確認や障害切り分け用の経路を、通常の deploy 手順に混ぜないことが大事になる。

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
  - `POSTGRES_*` から `DATABASE_URL` を組み立てる
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
- その後 `.release/current` に保存してある直前成功 SHA を使って、再度 `docker compose ... up -d django` を実行します。
- つまり rollback は `latest` ではなく、**EC2 が記録している前回成功版**に戻します。

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
- ここでの GitHub Actions の責務は「EC2 上の deploy の完了を待つこと」であり、コンテナ health 判定や rollback の実行はしません。

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
  - 各フェーズのログ出力、health check 待機、成功版 SHA の記録、rollback を持ちます。
- **[`scripts/bootstrap/sync-app-files.sh`](../../scripts/bootstrap/sync-app-files.sh)**
  - GitHub から `docker-compose.production.yml` と deploy 用スクリプトを取得します。
- **[`scripts/bootstrap/render-env-from-ssm.sh`](../../scripts/bootstrap/render-env-from-ssm.sh)**
  - SSM Parameter Store から `.envs/.production/.django` と `.postgres` を生成します。
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
- デプロイ先は単一 EC2 前提です。
  - Auto Scaling や複数台切り替えを前提にした構成ではありません。
- EC2 bootstrap は GitHub と SSM Parameter Store に依存します。
  - EC2 を再作成しても手作業は不要ですが、GitHub 到達性と Parameter Store 権限は必要です。
- direct SSM deploy のような補助経路は、通常運用の正規手順ではありません。
- SSH ベースの bootstrap 確認スクリプトは削除し、通常運用の導線から外しています。

---

## 9. 失敗時にどこを見るか

- まず次の順序で前提を切り分けます。
  - `production-config` apply 後に永続 SSM があるか
  - `production` apply 後に動的 SSM があるか
  - EC2 bootstrap が完了しているか
  - そのうえで GitHub Actions の deploy が失敗しているか
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
- bootstrap 自体を確認したいときは、EC2 の `/var/log/user-data.log` と `/opt/app/bin` / `.envs/.production` の生成状態を確認します。

### デプロイ前チェックリスト

workflow を回す前に、次を 1 回確認すると詰まりにくい。

1. `production-config/terraform.tfvars` を作成し、`django_secret_key` と `db_password` を設定した
2. `production-config` を apply した
3. `production` を apply した
4. `terraform output` で `github_actions_role_arn` と EC2 情報を確認した
5. GitHub Secrets に `AWS_ROLE_ARN` と `EC2_INSTANCE_ID` を入れた
6. EC2 bootstrap が完了した
7. 最初の 1 回は `workflow_dispatch` で手動実行して成功ログを確認した

---

## 参考

- 構築方法と導入経緯: [GitHub Actions CI/CD の構築](./06-github-actions-cicd.md)
- 改善テーマとしての位置づけ: [GitHub Actions デプロイパイプライン](../improvements/cicd-pipeline.md)
