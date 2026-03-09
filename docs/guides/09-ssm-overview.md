# SSM Parameter Store の全体像

このドキュメントは、現在の `shared/app` 構成で SSM Parameter Store がどう使われているかを整理したものです。

---

## まず 3 行で全体像

- `shared` が、長く残したい設定や secret と CloudFront 由来の共有値を SSM に保存する
- `app` が、インフラ作成のたびに変わる値を SSM に保存・更新する
- EC2 が SSM から値を取って `.env` を作り、Django コンテナはその `.env` を読んで起動する

## 1. なぜ SSM を使うのか

このシステムでは、学習用・ポートフォリオ用として `app` の `terraform destroy` / `terraform apply` を繰り返すことを想定している。

毎回変えたくない値:

- `DJANGO_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `DJANGO_ADMIN_URL`

作り直すたびに変わる値:

- ALB の DNS 名
- RDS の接続先ホスト名
- EC2 の private IP

さらに、CloudFront の URL は `shared` 側で維持し、`app` 停止時も公開入口を残す。

## 2. どこに保存されるか

SSM のプレフィックスは次です。

```text
/school-diary/production
```

主な保存先:

```text
/school-diary/production/django/...
/school-diary/production/postgres/...
/school-diary/production/system/...
```

正本:

- [shared/main.tf](/home/hirok/work/ANSWER_KEY/school_diary/terraform/environments/shared/main.tf)
- [app/parameter_store.tf](/home/hirok/work/ANSWER_KEY/school_diary/terraform/environments/app/parameter_store.tf)

## 3. 長寿命の値

`shared` が登録する値は、通常 destroy しない前提の共有設定。

代表例:

- `DJANGO_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `DJANGO_ADMIN_URL`
- `WEB_CONCURRENCY`
- `CLOUDFRONT_DOMAIN_NAME`
- `SERVICE_MODE`

このうち `DJANGO_SECRET_KEY` と `POSTGRES_PASSWORD` は `SecureString`。

## 4. 動的な値

`app` が登録する値は、インフラ再作成のたびに更新される。

代表例:

- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_SITE_URL`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `ALB_DNS_NAME`

`app` は `shared` が保存した `POSTGRES_PASSWORD` と `CLOUDFRONT_DOMAIN_NAME` を読み、動的 SSM を組み立てる。

## 5. 誰がいつ読むのか

### Terraform `app`

`app` 側 Terraform は、先に `shared` が保存した `POSTGRES_PASSWORD` と `CLOUDFRONT_DOMAIN_NAME` を SSM から読む。

```text
shared が SSM に固定値を保存
  ↓
app が SSM から固定値を取得
  ↓
RDS 作成と動的 SSM 更新に使う
```

### EC2 起動時

EC2 起動時の `user_data` で `render-env-from-ssm.sh` が呼ばれ、SSM から `.envs/.production/.django` と `.envs/.production/.postgres` が再生成される。

正本:

- [user_data.sh.tftpl](/home/hirok/work/ANSWER_KEY/school_diary/terraform/files/user_data.sh.tftpl)
- [render-env-from-ssm.sh](/home/hirok/work/ANSWER_KEY/school_diary/scripts/bootstrap/render-env-from-ssm.sh)

### GitHub Actions デプロイ時

GitHub Actions は SSM Parameter Store を直接読まない。SSM Run Command で EC2 にデプロイ命令を送り、EC2 が SSM を読み直す。

## 6. destroy/apply との関係

- `shared` を残したまま `app` だけ destroy / apply するなら、固定値 SSM と CloudFront URL は残る
- `app destroy` では動的 SSM は消える
- `shared destroy` を実行すると、固定値 SSM と CloudFront も消える

## 7. まとめ

現在の SSM の役割は次の 3 つ。

1. `shared` が固定値と共有値の正本になる
2. `app` が再生成される値を更新する
3. EC2 が毎回そこから `.env` を作る

つまり、Django 自体は SSM を直接読まず、EC2 が SSM を読んで環境変数へ橋渡ししている。
