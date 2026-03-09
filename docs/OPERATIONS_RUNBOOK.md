# 運用 Runbook

本書は、school_diary の障害検知後にどの順で確認し、どこまで切り分けるかをまとめた運用 runbook です。  
現状の構成と、今後追加予定の運用強化案の両方を踏まえています。

---

## 1. 基本方針

- まずサービス影響を確認する
- 次にどのレイヤで失敗しているかを切り分ける
- 監視イベントは severity に応じて扱いを分ける
- 復旧作業より先に、再現条件と影響範囲を把握する

---

## 2. Severity の考え方

### P1

- サービス停止
- ALB の UnHealthyHostCount >= 1
- EC2 StatusCheckFailed
- DB 接続不可

### P2

- 5xx 増加
- レスポンス時間悪化
- DB 接続数異常

### P3

- CPU 高騰
- ストレージ逼迫
- メモリ不足の予兆

---

## 3. 初動の順番

1. `/diary/health/` の応答確認
2. CloudWatch Alarm の発生内容確認
3. CloudWatch Logs の直近エラーログ確認
4. ALB / EC2 / RDS のどのレイヤか切り分け
5. 影響範囲と暫定対応可否を判断

---

## 4. シナリオ別 runbook

### ALB 5xx 増加

確認項目:

- `HTTPCode_ELB_5XX_Count`
- `HTTPCode_Target_5XX_Count`
- `TargetResponseTime`
- `UnHealthyHostCount`

切り分け:

- ELB 側 5xx なら ALB/ターゲット到達性を確認
- Target 5xx なら Django/Gunicorn 側の例外を確認
- レスポンス悪化が先行しているならアプリ/DB 負荷を疑う

次の確認:

- CloudWatch Logs の Django エラー
- EC2 CPU
- RDS 接続数、CPU、空き容量

### EC2 ヘルス異常

確認項目:

- `StatusCheckFailed`
- EC2 CPU
- アプリコンテナ状態

次の確認:

- Session Manager または SSH でインスタンス状態確認
- Docker コンテナログ確認
- 必要に応じて Gunicorn / コンテナ再起動

### RDS 接続数増加

確認項目:

- `DatabaseConnections`
- `CPUUtilization`
- `FreeableMemory`
- `FreeStorageSpace`

次の確認:

- アプリ側の例外有無
- コネクションリークの兆候
- 直近の負荷増加イベント有無

---

## 5. バックアップ / 復旧

現状の正本:

- RDS automated backup
- 保持期間 7 日
- Point-in-Time Recovery

復旧の考え方:

- DB 障害時は restore で新しい instance を起こす前提
- EC2 は再作成可能な前提で扱う
- アプリは Terraform、ECR イメージ、設定値から再構築する

今後追加するもの:

- AWS Backup
- Restore testing
- Backup Audit Manager

---

## 6. 今後の自動化候補

- CloudWatch Alarm -> OpsCenter
- EventBridge -> Lambda でイベント正規化
- Lambda -> ServiceNow PDI
- Systems Manager Automation による一次対応

---

## 7. 関連資料

- [ITOM_ROADMAP.md](./ITOM_ROADMAP.md)
- [SERVICENOW_INTEGRATION_PLAN.md](./SERVICENOW_INTEGRATION_PLAN.md)
- [TECHNICAL_SPECIFICATION.md](./TECHNICAL_SPECIFICATION.md)
