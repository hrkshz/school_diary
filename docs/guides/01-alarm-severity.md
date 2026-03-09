# CloudWatch アラームの重大度設計

## なぜやるか

CloudWatch アラームが鳴っても「これは今すぐ対応すべきか、明日でいいか」が分からないと、運用が回らない。
ITIL の Event Management では、イベントを重大度で分類し、対応の優先度を決める。
この分類があることで、後段の ServiceNow 連携でも severity をマッピングできる。

## 重大度の定義

| レベル | 意味 | 対応 | 例 |
|-------|------|------|---|
| P1 | サービス停止 | 即時対応 | EC2 StatusCheckFailed, ALB UnHealthyHost |
| P2 | 品質劣化 | 当日対応 | 5xx 増加, レスポンス悪化 |
| P3 | 予兆 | 計画対応 | CPU 高騰, ストレージ逼迫 |

## 何をしたか

### 手順 1: 既存アラームに重大度を追加

対象ファイル: `terraform/modules/cloudwatch/main.tf`

既存の 9 アラームそれぞれに 2 つの変更を加えた:

**変更 1: alarm_description に `[P1]` `[P2]` `[P3]` プレフィックスを追加**

```hcl
# Before
alarm_description = "Alert when EC2 status check fails"

# After
alarm_description = "[P1] Alert when EC2 status check fails"
```

なぜ description に入れるか: EventBridge がアラーム状態変化イベントをキャプチャしたとき、description はイベントの中身に含まれる。タグは含まれない。つまり EventBridge 側でフィルタリングしたいなら、description に重大度を入れるのが実用的。

**変更 2: tags に `Severity` を追加**

```hcl
tags = {
  Name        = "..."
  Environment = var.environment
  Severity    = "P1"  # 追加
}
```

タグはコスト配分、AWS コンソールでの検索、将来の AWS Config ルールで使う。

### 手順 2: 新規アラームを 2 個追加

同じファイルの末尾に追加:

**ALB ELB 5xx（P2）**
- メトリクス: `HTTPCode_ELB_5XX_Count`
- 意味: ALB 自体が返す 5xx（バックエンドではなくロードバランサの問題）
- 既存の `HTTPCode_Target_5XX_Count`（バックエンド側の 5xx）との違いを区別するため

**RDS FreeableMemory（P3）**
- メトリクス: `FreeableMemory`
- 意味: RDS インスタンスの空きメモリ
- 閾値: 128MB 未満（t3.micro は約 1GB なので 12% を切ったら警告）

### 手順 3: outputs.tf を更新

`terraform/modules/cloudwatch/outputs.tf` の `alarm_names` リストに新規 2 アラームを追加。

## 確認方法

```bash
cd terraform/environments/production
terraform validate  # 構文チェック
terraform plan      # 変更内容プレビュー（9 alarms changed, 2 added）
terraform apply     # AWS に反映
```

AWS コンソール → CloudWatch → Alarms で 11 個のアラームが表示され、それぞれにタグ `Severity` が付いていることを確認する。

## 全アラーム一覧

| アラーム名 | メトリクス | 閾値 | 重大度 |
|-----------|----------|------|--------|
| alb-5xx-errors | HTTPCode_Target_5XX_Count | > 10/min | P2 |
| alb-elb-5xx-errors | HTTPCode_ELB_5XX_Count | > 5/min | P2 |
| alb-unhealthy-host | UnHealthyHostCount | >= 1 | P1 |
| alb-response-time | TargetResponseTime | > 3s avg | P2 |
| ec2-cpu-high | CPUUtilization | > 80% | P3 |
| ec2-status-check-failed | StatusCheckFailed | >= 1 | P1 |
| rds-cpu-high | CPUUtilization | > 80% | P3 |
| rds-connections-high | DatabaseConnections | > 80 | P3 |
| rds-storage-low | FreeStorageSpace | < 2GB | P3 |
| rds-read-latency-high | ReadLatency | > 100ms | P2 |
| rds-freeable-memory-low | FreeableMemory | < 128MB | P3 |

## ブログで深掘りできるポイント

- ITIL の Event Management とは何か
- CloudWatch アラームの evaluation_periods と period の関係
- `treat_missing_data = "notBreaching"` の意味と設計判断
- P1/P2/P3 の閾値をどう決めたか（t3.micro の制約）
