# Terraform 残存性監査

この文書は、`shared/app` 分離を入れる前の旧構成を確認した監査メモです。現行の運用手順は [07-terraform-apply.md](/home/hirok/work/ANSWER_KEY/school_diary/docs/guides/07-terraform-apply.md) を正本とします。

ステータス: 完了
優先度: 中

---

## 目的

- `terraform destroy` / `terraform apply` を繰り返す前提で、何が残り、何が消えるかを明確にする
- 固定値が残る根拠が state 分離なのか、Terraform の削除保護なのかを切り分ける
- CloudFront と SSM Parameter Store が現状「データの元」として残る設計かどうかを確認する

## 結論

- `production` だけを `terraform destroy` / `terraform apply` するなら、`production-config` 管理の固定値 SSM は残る
- `production-config` を `terraform destroy` すれば、固定値 SSM も削除される
- 固定値が残る根拠は `production-config` と `production` の state 分離であり、`prevent_destroy` などの lifecycle 保護ではない
- CloudFront は現状 `production` 管理下の通常リソースなので、`production` を destroy すると削除される
- 動的 SSM パラメータも `production` 管理下なので、`production` を destroy すると削除される

## 1. `production-config destroy` と `production destroy` の違い

### `production-config` が管理しているもの

`production-config` は、長寿命設定と secret を SSM Parameter Store に登録する。

正本:

- [terraform/environments/production-config/main.tf](/home/hirok/work/ANSWER_KEY/school_diary/terraform/environments/production-config/main.tf)
- [docs/guides/09-ssm-overview.md](/home/hirok/work/ANSWER_KEY/school_diary/docs/guides/09-ssm-overview.md)

ここで管理している代表例:

- `DJANGO_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `DJANGO_ADMIN_URL`
- `WEB_CONCURRENCY`

したがって `production-config` を destroy すると、これらの固定値 SSM も Terraform 管理対象として削除される。

### `production` が管理しているもの

`production` は、VPC、ALB、EC2、RDS、CloudFront などのインフラ本体と、再生成される動的 SSM を管理する。

正本:

- [terraform/environments/production/main.tf](/home/hirok/work/ANSWER_KEY/school_diary/terraform/environments/production/main.tf)
- [terraform/environments/production/parameter_store.tf](/home/hirok/work/ANSWER_KEY/school_diary/terraform/environments/production/parameter_store.tf)

ここで管理している代表例:

- CloudFront distribution
- ALB
- EC2
- RDS
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_SITE_URL`
- `POSTGRES_HOST`

したがって `production` を destroy すると、これらの AWS リソースと動的 SSM は削除される。

## 2. 固定値が残る根拠

固定値が残る理由は、同じ state の中で削除保護されているからではない。  
現状の根拠は、`production-config` と `production` を別ディレクトリ・別 state として分離している点にある。

正本:

- [terraform/environments/production-config/backend.tf](/home/hirok/work/ANSWER_KEY/school_diary/terraform/environments/production-config/backend.tf)
- [terraform/environments/production/backend.tf](/home/hirok/work/ANSWER_KEY/school_diary/terraform/environments/production/backend.tf)
- [docs/guides/07-terraform-apply.md](/home/hirok/work/ANSWER_KEY/school_diary/docs/guides/07-terraform-apply.md)

運用前提は次のとおり:

1. 先に `production-config` を apply して固定値を SSM に登録する
2. その後 `production` を apply してインフラと動的 SSM を作る
3. 再構築時は `production-config` を残し、`production` だけを destroy / apply する

この設計なら、`production` を再作成しても `POSTGRES_PASSWORD` などの固定値を再利用できる。  
実際に `production` は、固定パスワードを SSM から読み出して RDS を作成している。

正本:

- [terraform/environments/production/parameter_store.tf](/home/hirok/work/ANSWER_KEY/school_diary/terraform/environments/production/parameter_store.tf)

## 3. lifecycle 保護の有無

Terraform 定義を確認した限り、`prevent_destroy`、retain、skip destroy 相当の明示的な保護は見当たらない。

確認対象:

- `terraform/environments/production-config/`
- `terraform/environments/production/`
- `terraform/modules/`

監査結果:

- SSM Parameter Store に `lifecycle { prevent_destroy = true }` は設定されていない
- CloudFront distribution に削除保護は設定されていない
- RDS は `deletion_protection = false`
- ALB も `enable_deletion_protection = false`

正本:

- [terraform/modules/cloudfront/main.tf](/home/hirok/work/ANSWER_KEY/school_diary/terraform/modules/cloudfront/main.tf)
- [terraform/modules/rds/main.tf](/home/hirok/work/ANSWER_KEY/school_diary/terraform/modules/rds/main.tf)
- [terraform/modules/alb/main.tf](/home/hirok/work/ANSWER_KEY/school_diary/terraform/modules/alb/main.tf)

つまり、現状の「残る / 消える」は Terraform の保護設定ではなく、どの state がそのリソースを持っているかで決まる。

## 4. CloudFront と SSM は「データの元」として残るか

### 固定値 SSM

固定値 SSM は、`production-config` を残す運用なら「データの元」として残る。  
ただし `production-config` 自体を destroy すれば削除されるため、恒久保護ではない。

### 動的 SSM

動的 SSM は `production` 管理下なので、`production destroy` で削除される。  
再 apply 後に、最新の ALB DNS、CloudFront ドメイン、RDS endpoint を元に再登録される。

### CloudFront

CloudFront は現状 `production` 配下の通常リソースであり、残らない。  
`production destroy` を実行すると distribution は削除対象になるため、`dxxxxxxxxxxxx.cloudfront.net` も維持されない。

これは既存の改善メモでも「将来やりたいこと」として扱われている。

正本:

- [docs/improvements/service-availability-control.md](/home/hirok/work/ANSWER_KEY/school_diary/docs/improvements/service-availability-control.md)

この改善メモには「CloudFront のディストリビューションは削除しない」とあるが、現状は未実装である。

## 5. 監査時の注意

- 今回の確認範囲はリポジトリ上の Terraform 定義とドキュメントに限定している
- 実 AWS 環境の state や手動変更の有無は確認していない
- backend はコメントアウトされており、現状説明では local state 前提になっている
- local state を失うと「残る設計」であっても Terraform から安全に再利用できなくなる

## まとめ

現状の設計は、「固定値 SSM を `production-config` に分離し、再作成対象を `production` に寄せる」ことで destroy / apply の再利用性を確保している。  
一方で CloudFront や動的 SSM は `production` に含まれており、削除保護もないため、`production destroy` では残らない。  
そのため、「残したい値が残る」は成立するが、「CloudFront や全 SSM が常にデータの元として残る」状態にはまだなっていない。
