# EventBridge によるイベント集約

## なぜやるか

CloudWatch アラームは「通知」しかできない（SNS → メール）。
EventBridge を挟むと、アラームを「イベント」として扱える。
イベントにすると:
- フィルタリングできる（自分のプロジェクトのアラームだけ拾う）
- 複数のターゲットに送れる（SNS, Lambda, SQS, Step Functions）
- 将来 Lambda でイベントを加工して ServiceNow に送れる

```
Before: CloudWatch Alarm → SNS → メール（通知だけ）
After:  CloudWatch Alarm → EventBridge → SNS（今）
                                       → Lambda（Phase 2 で追加予定）
                                       → ServiceNow（Phase 6 で追加予定）
```

## 何をしたか

### 手順 1: EventBridge モジュールを新規作成

`terraform/modules/eventbridge/` ディレクトリを作成し、3 ファイルを配置:

```
terraform/modules/eventbridge/
├── main.tf        # EventBridge ルールとターゲット
├── variables.tf   # 入力変数
└── outputs.tf     # 出力
```

### 手順 2: EventBridge ルールの定義

```hcl
resource "aws_cloudwatch_event_rule" "alarm_state_change" {
  name = "${var.project_name}-${var.environment}-alarm-state-change"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]              # CloudWatch からのイベント
    detail-type = ["CloudWatch Alarm State Change"] # アラーム状態変化イベント
    detail = {
      state = {
        value = ["ALARM"]                          # ALARM 状態になったときだけ
      }
      alarmName = [{
        prefix = "${var.project_name}-${var.environment}"  # 自プロジェクトのアラームだけ
      }]
    }
  })
}
```

**ポイント: `alarmName` のプレフィックスフィルタ**

AWS アカウント内の全アラームの状態変化が EventBridge に流れてくる。
他のプロジェクトや別の用途のアラームを拾わないよう、アラーム名のプレフィックスでフィルタする。
これが機能するのは、全アラーム名を `${project_name}-${environment}-...` で統一しているから。

### 手順 3: ターゲットの設定

```hcl
resource "aws_cloudwatch_event_target" "alarm_to_sns" {
  rule      = aws_cloudwatch_event_rule.alarm_state_change.name
  target_id = "send-to-sns"
  arn       = var.sns_topic_arn  # 既存の SNS トピックを再利用
}
```

Phase 2 では、ここに Lambda をターゲットとして追加する。

### 手順 4: SNS Topic Policy の追加

EventBridge から SNS に Publish するには、SNS 側で許可が必要。
`terraform/modules/cloudwatch/main.tf` に `aws_sns_topic_policy` を追加:

```hcl
resource "aws_sns_topic_policy" "alarms" {
  arn = aws_sns_topic.alarms.arn

  policy = jsonencode({
    Statement = [
      {
        Sid       = "AllowCloudWatchAlarms"
        Effect    = "Allow"
        Principal = { Service = "cloudwatch.amazonaws.com" }
        Action    = "sns:Publish"
        Resource  = aws_sns_topic.alarms.arn
      },
      {
        Sid       = "AllowEventBridge"
        Effect    = "Allow"
        Principal = { Service = "events.amazonaws.com" }
        Action    = "sns:Publish"
        Resource  = aws_sns_topic.alarms.arn
      }
    ]
  })
}
```

**なぜ 2 つの Principal が必要か:**
- `cloudwatch.amazonaws.com`: 既存のアラーム → SNS 通知（これがないと既存の通知が壊れる）
- `events.amazonaws.com`: EventBridge → SNS 通知（今回追加分）

### 手順 5: production 環境にモジュールを追加

`terraform/environments/production/main.tf`:

```hcl
module "eventbridge" {
  source        = "../../modules/eventbridge"
  project_name  = var.project_name
  environment   = var.environment
  sns_topic_arn = module.cloudwatch.sns_topic_arn
}
```

## 確認方法

AWS コンソール → EventBridge → Rules で `school-diary-production-alarm-state-change` が表示される。

実際にアラームが ALARM 状態になると:
1. CloudWatch Alarm が状態変化
2. EventBridge がイベントをキャプチャ
3. SNS にイベントを転送
4. メール通知

## ブログで深掘りできるポイント

- EventBridge のイベントパターンマッチングの仕組み
- CloudWatch Alarm State Change イベントの JSON 構造
- EventBridge vs SNS の使い分け
- 将来の Lambda ターゲット追加（Phase 2）との関係
