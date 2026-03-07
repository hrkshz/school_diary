# デプロイ参照情報

本書は、公開時に更新する URL と、Terraform から確認する値を一元管理するためのドキュメントです。

## 1. 公開時に更新する場所

公開前に更新するのは、原則として **このドキュメントの「Application Base URL」だけ** です。

### Application Base URL

`https://d11e79eaa3tdud.cloudfront.net`

### 派生 URL

- **Admin URL**: `{Application Base URL}/admin/`
- **Login URL**: `{Application Base URL}/accounts/login/`
- **Health Check URL**: `{Application Base URL}/diary/health/`

## 2. Terraform で確認する値

```bash
cd terraform/environments/production
terraform output
```

確認する output:

- `cloudfront_domain_name`
- `alb_dns_name`
- `ec2_public_ip`
- `rds_endpoint`

CloudFront ドメインをブラウザ用 URL にするときは、以下の形式を使います。

```text
https://<cloudfront_domain_name>
```

## 3. 運用上の注意

- この環境は常時稼働前提ではなく、必要なときだけ起動する運用です。
- Terraform で再構築した場合、CloudFront や ALB の URL が変わることがあります。
- そのため、他ドキュメントには固定 URL を直接書かず、本書を参照する形にします。

## 4. 公開前チェック

1. `terraform output` で最新の `cloudfront_domain_name` を確認
2. 本書の `Application Base URL` を更新
3. Health Check URL にアクセスして応答を確認
4. README と主要資料が本書を参照していることを確認

## 5. 最終更新

- **Last Checked Date**: 2026-03-07
