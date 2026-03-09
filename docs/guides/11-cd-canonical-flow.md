# CD 正規フローの入口

このドキュメントは、**今この repo で本当に動いている正規の deploy 経路だけ**を最短で把握するための入口です。  
新人が最初に読む前提で、責務分担、正本ファイル、実行順、失敗時に最初に見る場所を固定しています。

---

## 先に全体像

```text
production-config
  -> production
  -> EC2 user_data bootstrap
  -> GitHub Actions
  -> SSM Run Command
  -> EC2 上の ssm-deploy.sh
```

この経路以外は、通常運用の正規手順ではありません。

---

## 責務表

| 役割 | 正本ファイル | 実行タイミング | 入力 | 出力 | 失敗時にまず見る場所 |
|---|---|---|---|---|---|
| Terraform: 永続設定投入 | `terraform/environments/production-config` | 初回構築時、secret 変更時 | `terraform.tfvars` | SSM の永続 secret / 永続設定 | `terraform apply` 出力 |
| Terraform: インフラ構築 | `terraform/environments/production` | 初回構築時、再構築時 | `terraform.tfvars`、SSM の `POSTGRES_PASSWORD` | AWS リソース、動的 SSM 値 | `terraform apply` 出力 |
| EC2 bootstrap | `terraform/files/user_data.sh.tftpl` | EC2 初回起動時 | GitHub raw、SSM Parameter Store | `/opt/app/bin`、`.envs/.production/*`、初回 deploy 試行 | `/var/log/user-data.log` |
| GitHub Actions | `.github/workflows/deploy.yml` | `main` push、`workflow_dispatch` | repo、OIDC、ECR、EC2 instance id | 新イメージ push、SSM command 実行、`COMMAND_ID` 出力、最終 health 確認 | GitHub Actions job log |
| EC2 deploy 実行 | `scripts/ssm-deploy.sh` | GitHub Actions から呼び出し | ECR image、`.envs/.production/*`、`DEPLOY_RUN_ID`、`DEPLOY_SHA` | pull、migrate、up、health、rollback、release 記録、trace 記録 | SSM command stdout / stderr |

---

## 実行順

| 順番 | 何をするか | 正本 |
|---|---|---|
| 1 | 永続 secret / 永続設定を SSM に登録する | `production-config` |
| 2 | インフラを作り、動的 SSM 値を更新する | `production` |
| 3 | EC2 が user_data で bootstrap する | `user_data.sh.tftpl` |
| 4 | GitHub Actions が Docker image を build / push する | `deploy.yml` |
| 5 | GitHub Actions が SSM Run Command で deploy を開始する | `deploy.yml` |
| 6 | EC2 上の `ssm-deploy.sh` が本番反映を完了する | `scripts/ssm-deploy.sh` |
| 7 | ALB `/diary/health/` を確認する | `deploy.yml` |

---

## 何を見ればよいか

- Terraform 全体: [07-terraform-apply.md](./07-terraform-apply.md)
- GitHub Actions から AWS までの流れ: [08-current-cd-flow.md](./08-current-cd-flow.md)
- SSM の保存内容と取得の流れ: [09-ssm-overview.md](./09-ssm-overview.md)
- 設定値全体の地図: [10-configuration-map.md](./10-configuration-map.md)
- 失敗時の切り分け: [12-cd-troubleshooting.md](./12-cd-troubleshooting.md)

---

## Trace の基準

- GitHub Actions は `COMMAND_ID` を必ず出す
- GitHub Actions の verify step は `run id / sha / command id` をまとめて表示する
- EC2 は `.release/current`、`.release/previous`、`.release/last-run-id`、`.release/last-deploy-sha` を更新する
- 観測順は `GitHub run -> SSM command -> EC2 deploy log -> container health -> ALB health`
