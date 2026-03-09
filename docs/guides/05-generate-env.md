# 環境変数の自動生成

## なぜやるか

`terraform apply` でインフラを構築すると、EC2 の IP、ALB の DNS 名、CloudFront のドメインなどが新しくなる。
これらの値は Django の環境変数（`.envs/.production/.django`）にも反映する必要がある。

手動で毎回書き換えると:
- 書き間違える
- 古い値のまま起動してエラーになる
- 何を変えたか分からなくなる

## 何をしたか

### scripts/generate-env.sh の作成

SSM Parameter Store から値を取得し、`.envs/.production/.django` と `.envs/.production/.postgres` を自動生成するスクリプトを作成した。

### 仕組み

```
SSM Parameter Store → `.env` ファイルを生成
```

### 使い方

```bash
# プロジェクトルートで実行
bash scripts/generate-env.sh
```

これだけで以下が自動的に更新される:
- `DJANGO_ALLOWED_HOSTS`（ALB DNS, CloudFront ドメイン）
- `DJANGO_SITE_URL`
- `DJANGO_AWS_STORAGE_BUCKET_NAME`
- PostgreSQL 接続情報
- 永続設定 / secret

### スクリプトの動作

1. `aws ssm get-parameter` で必要な値を取得
2. `.envs/.production/.django` と `.envs/.production/.postgres` を上書き生成
3. Django コンテナの entrypoint が `POSTGRES_*` から `DATABASE_URL` を組み立てる

### 設計判断

**Q: なぜ secret を SSM に残すのか?**
A: `terraform destroy` を繰り返しても、`DJANGO_SECRET_KEY` や `POSTGRES_PASSWORD` を毎回手入力し直さずに再利用できるため。

**Q: なぜ `DATABASE_URL` を SSM に置かないのか?**
A: DB 接続情報の正本を `POSTGRES_*` に寄せ、コンテナ起動時に `DATABASE_URL` を組み立てる方が二重管理を避けやすいため。

## 確認方法

```bash
# 実行
bash scripts/generate-env.sh

# 出力例
# 環境変数ファイルを生成しました:
#   .envs/.production/.django
#   .envs/.production/.postgres
#
# 内容確認
cat .envs/.production/.django
```

## ブログで深掘りできるポイント

- SSM Parameter Store を長寿命設定ストアとして使う設計
- 環境変数管理のベストプラクティス（.env vs SSM Parameter Store vs Secrets Manager）
- IaC とアプリ設定の境界をどう設計するか
