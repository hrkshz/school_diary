# ServiceNow PDI 連携計画

本書は、school_diary の AWS 運用イベントを ServiceNow PDI に連携し、ITOM 寄りの構成として示すための計画書です。  
目的は、監視イベントを ServiceNow 側の Incident / Event / CMDB 文脈へつなげることです。

---

## 1. 目的

- AWS 側の障害検知を ServiceNow 側に届ける
- イベントを正規化し、重複起票しにくい形にする
- 将来的に CMDB / Config 連携へ拡張できる設計にする

---

## 2. 推奨アーキテクチャ

最初に採用する候補:

```text
CloudWatch Alarm
  -> EventBridge
  -> Lambda
  -> ServiceNow PDI Table API
```

この構成を優先する理由:

- PDI で再現しやすい
- 実装対象が明確
- payload を自分で制御できる
- Event Management と Incident 起票の両方に広げやすい

---

## 3. 連携対象

初期対象:

- P1 アラーム
- P2 アラーム

例:

- ALB UnHealthyHostCount
- EC2 StatusCheckFailed
- ALB 5xx 増加
- RDS 接続数異常

P3 は原則 AWS 側で保持し、最初は ServiceNow へ送らない

---

## 4. Lambda で正規化する項目

- `event_type`
- `severity`
- `source`
- `resource_type`
- `resource_id`
- `environment`
- `summary`
- `details_url`
- `runbook_id`
- `dedupe_key`

`dedupe_key` は、同じアラームが短時間で重複起票されないようにするための correlation 用 ID とする

---

## 5. ServiceNow 側マッピング案

- `short_description`: 監視イベント要約
- `description`: 詳細本文
- `severity`: AWS 側 severity を変換
- `impact`: サービス影響
- `urgency`: 初動優先度
- `source`: `AWS`
- `correlation_id`: `dedupe_key`
- `cmdb_ci` または resource reference: 対象リソース

---

## 6. 実装順序

### Step 1

- EventBridge から Lambda を起動
- Lambda が正規化済み JSON を出力

### Step 2

- ServiceNow PDI に対して Table API で POST
- P1/P2 のみ起票

### Step 3

- dedupe の調整
- 既存 open event / incident との相関設計

### Step 4

- OpsCenter や Connector を比較し、標準連携の位置づけを整理

### Step 5

- AWS Config / inventory 情報の CMDB 取り込みを検討

---

## 7. 代替案

### AWS Service Management Connector

長所:

- AWS 標準連携を使える
- ServiceNow 連携に関する理解を示しやすい

短所:

- PDI での再現性や構成依存の確認が必要
- 最初の見せ場としては、Lambda 直連携より制御しにくい

### OpsCenter 経由

長所:

- AWS 側の運用イベント整理に向く
- Runbook と相性が良い

短所:

- ServiceNow に直接連携するには中継設計が要る

---

## 8. 後段の拡張

- AWS Config -> ServiceNow CMDB
- Systems Manager Automation と Change Enablement の接続
- ServiceNow 側から再実行や確認リンクを返す双方向連携

---

## 9. 関連資料

- [ITOM_ROADMAP.md](./ITOM_ROADMAP.md)
- [OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md)
