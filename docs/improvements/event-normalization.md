# イベント正規化

ステータス: 予定
優先度: 高

---

## なぜやるか

- EventBridge でキャプチャしたアラームイベントを、ServiceNow に渡せる形に正規化する
- 単なる通知ではなく、重大度・リソース情報・dedupe_key を付与した構造化イベントにする
- Phase 6（ServiceNow PDI 連携）の直接の前提

## 何をするか

- Lambda 関数（Python）を作成
- EventBridge のターゲットに Lambda を追加
- Lambda で以下を付与して SNS/SQS に転送:
  - `severity` / `source` / `resource_type` / `resource_id`
  - `environment` / `summary` / `details_url`
  - `runbook_id` / `dedupe_key`

## Terraform で追加するリソース

- `aws_lambda_function`
- `aws_iam_role`（Lambda 実行ロール）
- `aws_lambda_permission`（EventBridge からの呼び出し許可）
- `aws_cloudwatch_event_target`（EventBridge → Lambda）

## コスト

無料枠内（Lambda: 月 100 万リクエスト、400,000 GB 秒まで無料）

## 備考

- EC2 夜間停止（#9）の Lambda と実装パターンが共通
- 同時に進めると効率的
