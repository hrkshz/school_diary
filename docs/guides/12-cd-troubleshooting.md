# CD 切り分け表

このドキュメントは、**処理段階ごとにどのファイルとログを見ればよいか**を最短で辿るための表です。  
症状ベースではなく、正規フローのどこで止まったかで切り分けます。

---

## 処理段階別の切り分け

| 処理段階 | まず見るファイル | まず見るログ | 期待状態 |
|---|---|---|---|
| `production-config apply` 失敗 | `terraform/environments/production-config` | `terraform apply` 出力 | 永続 secret / 永続設定が SSM に登録される |
| `production apply` 失敗 | `terraform/environments/production` | `terraform apply` 出力 | AWS リソース作成と動的 SSM 更新が完了する |
| `user_data bootstrap` 失敗 | `terraform/files/user_data.sh.tftpl` | EC2 `/var/log/user-data.log` | `/opt/app/bin` と `.envs/.production/*` が生成される |
| `GitHub Actions build` 失敗 | `.github/workflows/deploy.yml`、`compose/production/django/Dockerfile` | GitHub Actions `Build and push Docker image` | ECR に `${github.sha}` と `latest` が push される |
| `SSM command` 失敗 | `.github/workflows/deploy.yml`、`scripts/ssm-deploy.sh` | GitHub Actions `Deploy to EC2 via SSM` の `COMMAND_ID` と invocation log | SSM command が `Success` で終わる |
| `container health` 失敗 | `scripts/ssm-deploy.sh`、`docker-compose.production.yml` | SSM stdout/stderr、EC2 上の container log | `docker inspect` の health が `healthy` になる |
| `ALB health` 失敗 | `.github/workflows/deploy.yml` | GitHub Actions `Verify deployment` | `/diary/health/` が `200` を返す |

---

## 典型的な見方

### `GitHub Actions build` で止まる

- まず `deploy.yml` の build step を開く
- 次に Dockerfile 内の build-time 処理を見る
- 期待状態:
  - Docker image build 完了
  - ECR push 完了

### `SSM command` で止まる

- まず GitHub Actions の `COMMAND_ID`
- 次に `Fetch SSM invocation logs` の出力
- 次に `scripts/ssm-deploy.sh`
- 期待状態:
  - pull
  - migrate
  - `docker compose up -d`
  - health wait
  - success

### `container health` で止まる

- まず `scripts/ssm-deploy.sh` の health wait 部分
- 次に `docker-compose.production.yml` の healthcheck
- 期待状態:
  - Django container が `healthy`
  - rollback に入らない

---

## 補足

- direct SSM deploy や secret 回収は、この表の通常運用には含めません。
- 迷ったら、先に [11-cd-canonical-flow.md](./11-cd-canonical-flow.md) で正規フローを確認してください。
- EC2 側では `.release/current`、`.release/previous`、`.release/last-run-id`、`.release/last-deploy-sha` が trace の起点になります。
