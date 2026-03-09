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

Terraform の output から値を取得し、`.envs/.production/.django` と `.envs/.production/.postgres` を自動生成するスクリプトを作成した。

### 仕組み

```
terraform output -json → jq で値を抽出 → .env ファイルを生成
```

### 使い方

```bash
# プロジェクトルートで実行
bash scripts/generate-env.sh
```

これだけで以下が自動的に更新される:
- `DJANGO_ALLOWED_HOSTS`（EC2 IP, ALB DNS, CloudFront ドメイン）
- `DATABASE_URL`（RDS エンドポイント）
- `EC2_INSTANCE_ID`
- `DJANGO_AWS_STORAGE_BUCKET_NAME`
- PostgreSQL 接続情報

### スクリプトの動作

1. `terraform output -json` で全出力を JSON で取得
2. `jq` で必要な値を抽出
3. `terraform.tfvars` から DB パスワードを取得（output に含まれないため）
4. `aws ec2 describe-instances` で EC2 Instance ID を取得
5. 既存の `DJANGO_SECRET_KEY` を保持（あれば）
6. `.envs/.production/.django` と `.envs/.production/.postgres` を上書き生成

### 設計判断

**Q: なぜ Terraform output に DB パスワードを含めないのか?**
A: `terraform output` は平文で出力される。パスワードは `sensitive = true` にしても `terraform output -json` では見える。tfvars から直接読む方がスコープが狭い。

**Q: なぜ DJANGO_SECRET_KEY を保持するのか?**
A: SECRET_KEY を変えるとセッションが全て無効になる。インフラ再構築のたびにユーザーがログアウトされるのは望ましくない。

## 確認方法

```bash
# 実行
bash scripts/generate-env.sh

# 出力例
# 環境変数ファイルを生成しました:
#   .envs/.production/.django
#   .envs/.production/.postgres
#
# 主要値:
#   EC2 IP:         18.183.184.98
#   ALB DNS:        school-diary-production-alb-xxx.ap-northeast-1.elb.amazonaws.com
#   CloudFront:     dXXXXXXXXXX.cloudfront.net
#   ...

# 内容確認
cat .envs/.production/.django
```

## ブログで深掘りできるポイント

- Terraform output の活用パターン
- 環境変数管理のベストプラクティス（.env vs SSM Parameter Store vs Secrets Manager）
- シークレット管理の段階（今回 → SSM → Secrets Manager）
- IaC とアプリ設定の境界をどう設計するか
