# CloudWatch ダッシュボードの構築

## なぜやるか

アラームは「異常時に通知する」仕組み。ダッシュボードは「今の状態を見る」仕組み。
障害時にログインして「何が起きているか」を即座に把握するためにダッシュボードが必要。
AWS の無料枠はダッシュボード 3 個まで。

## 何をしたか

### 作成したダッシュボード

| ダッシュボード | 目的 | 表示メトリクス |
|-------------|------|-------------|
| availability | サービスは生きているか | HealthyHostCount, UnHealthyHostCount, StatusCheckFailed, RequestCount |
| db-health | DB は健全か | CPU, Connections, FreeStorageSpace, FreeableMemory, ReadLatency |
| error-trends | エラーは増えているか | Target 5XX, ELB 5XX, Target 4XX |

### 手順 1: dashboards.tf を新規作成

`terraform/modules/cloudwatch/dashboards.tf` を新規作成した。
`main.tf` に追加しなかった理由: main.tf はアラーム定義で既に 300 行近くあり、責務を分離するため。
同じモジュール内なので変数は共有できる。

### 手順 2: ダッシュボードの定義

Terraform では `aws_cloudwatch_dashboard` リソースを使う。
ダッシュボードの中身は JSON で定義するが、生の JSON ではなく `jsonencode()` を使って HCL のマップから生成する。

```hcl
resource "aws_cloudwatch_dashboard" "availability" {
  dashboard_name = "${var.project_name}-${var.environment}-availability"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0        # ダッシュボード上の位置（横）
        y      = 0        # ダッシュボード上の位置（縦）
        width  = 12       # 幅（最大24）
        height = 6        # 高さ
        properties = {
          title   = "ALB Host Health"
          region  = "ap-northeast-1"
          metrics = [
            # [名前空間, メトリクス名, ディメンション名, ディメンション値, オプション]
            ["AWS/ApplicationELB", "HealthyHostCount", "TargetGroup", var.alb_target_group_arn_suffix, "LoadBalancer", var.alb_arn_suffix, { stat = "Average", label = "Healthy Hosts" }]
          ]
          period  = 60
          view    = "timeSeries"
        }
      }
    ]
  })
}
```

**jsonencode() を使う利点:**
- Terraform 変数（`var.alb_arn_suffix` 等）を直接埋め込める
- HCL の構文チェックが効く
- フォーマットが崩れにくい

### 手順 3: outputs.tf にダッシュボード ARN を追加

```hcl
output "dashboard_arns" {
  value = [
    aws_cloudwatch_dashboard.availability.dashboard_arn,
    aws_cloudwatch_dashboard.db_health.dashboard_arn,
    aws_cloudwatch_dashboard.error_trends.dashboard_arn,
  ]
}
```

## コスト

- 無料枠: 3 個まで → ちょうど 3 個なので **無料**
- 4 個目からは $3/月/個

## 確認方法

AWS コンソール → CloudWatch → Dashboards で 3 つのダッシュボードが表示される。
アプリが動いていなくてもダッシュボードは表示される（データが空なだけ）。

## ブログで深掘りできるポイント

- CloudWatch ダッシュボードの widget 配置（x, y, width, height のグリッドシステム）
- metrics 配列の構造（名前空間、メトリクス名、ディメンション）
- stat の種類（Average, Sum, Maximum, p99）
- 無料枠 3 個でどのダッシュボードを選ぶかの判断基準
