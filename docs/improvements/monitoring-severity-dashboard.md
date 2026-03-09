# アラーム重大度分類 + ダッシュボード整備

ステータス: **完了**（2026-03-09）
コミット: `89f76c2`

---

## なぜやるか

- 既存アラームに重大度分類がなく、EventBridge / ServiceNow 連携の土台がない
- ダッシュボードがなく、AWS 側での可視化手段がない
- Phase 2（Lambda 正規化）、Phase 6（ServiceNow 連携）の前提

## 何をしたか

- 既存アラーム 9 個に重大度タグ（P1/P2/P3）追加
- 新規アラーム 2 個追加（ALB ELB 5xx、RDS FreeableMemory）
- CloudWatch ダッシュボード 3 個追加（availability, db-health, error-trends）
- EventBridge モジュール新規作成（アラーム状態変化 → SNS 転送）
- SNS Topic Policy 追加（CloudWatch + EventBridge Publish 許可）

## 変更ファイル

- `terraform/modules/cloudwatch/main.tf` - severity 追加、新規アラーム、SNS policy
- `terraform/modules/cloudwatch/dashboards.tf` - 新規（ダッシュボード 3 個）
- `terraform/modules/cloudwatch/outputs.tf` - 出力追加
- `terraform/modules/eventbridge/` - 新規モジュール（main.tf, variables.tf, outputs.tf）
- `terraform/environments/production/main.tf` - eventbridge モジュール追加
- `terraform/environments/production/outputs.tf` - 出力追加

## コスト

無料枠内（ダッシュボード 3 個、アラーム 11 個）
