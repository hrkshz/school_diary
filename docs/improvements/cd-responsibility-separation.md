# CD 動線の一本化

ステータス: **予定**

---

## なぜやるか

- deploy の責務が GitHub Actions と EC2 側にまたがり、初心者が正規経路を追いにくい
- 移行時に使った補助経路が残っていると、通常運用と障害切り分けが混ざる
- ベストプラクティスとして、Terraform / SSM / EC2 / GitHub Actions の責務を固定したい

## 固定する責務

- Terraform: インフラと設定の正本
- SSM: 本番設定の保管庫
- EC2: 実行主体
- GitHub Actions: オーケストレーター

## 正規の deploy 経路

```text
production-config
  -> SSM に永続 secret / 永続設定を登録
production
  -> インフラ作成 + 動的 SSM 値を更新
EC2 user_data
  -> bootstrap ファイル取得
  -> SSM から .env 生成
  -> 初回 deploy 試行
GitHub Actions
  -> Docker build / ECR push
  -> SSM Run Command で deploy 開始
EC2 scripts/ssm-deploy.sh
  -> pull / migrate / up / health / rollback
```

## 何を整理するか

- `ssm-deploy.sh` を本番反映の唯一の正本にする
- `deploy.yml` は build / push / deploy 起動 / 最終確認だけに寄せる
- SSH ベースの bootstrap 補助スクリプトは削除し、正規経路から外す
- direct SSM deploy や secret 回収は移行メモへ隔離し、通常手順から外す

## 前提資料

- [docs/guides/07-terraform-apply.md](../guides/07-terraform-apply.md)
- [docs/guides/08-current-cd-flow.md](../guides/08-current-cd-flow.md)
- [docs/guides/10-configuration-map.md](../guides/10-configuration-map.md)
- [docs/guides/09-ssm-overview.md](../guides/09-ssm-overview.md)
