# ITOM / ServiceNow 連携ロードマップ

本書は、school_diary を単なる業務 Web アプリではなく、運用・監視・イベント管理・復旧設計まで含めて改善していくためのロードマップです。  
目的は、ServiceNow / ITOM / ITIL 文脈で求められる考え方を、AWS 上の実装とドキュメントの両面で示せる状態にすることです。

---

## 1. 目的

- アプリ運用を「監視して終わり」ではなく、検知、分類、起票、初動、復旧までつながる形にする
- CloudWatch / EventBridge / Lambda / Systems Manager / AWS Backup / AWS Config を段階的に導入する
- 将来的に ServiceNow PDI と連携し、ITOM に近い運用イベント処理を実演できるようにする
- ITIL の Incident Management、Event Management、Change Enablement、Service Continuity の考え方を設計に反映する

---

## 2. 現状

現在の repo と Terraform で確認できる事実:

- AWS 構成は CloudFront / ALB / EC2 / RDS / S3 / ECR / SES / CloudWatch
- CloudWatch アラームは一部 Terraform 管理済み
  - ALB: 5xx、UnHealthyHostCount、TargetResponseTime
  - EC2: CPU、StatusCheckFailed
  - RDS: CPU、DatabaseConnections、FreeStorageSpace
- CloudWatch Logs の集約あり
- RDS は automated backup を有効化し、保持期間は 7 日
- アプリ側には `/diary/health/` の health check がある

不足しているもの:

- 重大度設計
- イベント正規化
- 運用 runbook
- 復旧演習の仕組み
- 構成変更履歴の可視化
- ServiceNow PDI 連携

---

## 3. ロードマップ

### Phase 0: docs を正本化する

目的:

- 実装前に、何をどの順で足すかを決める
- 既存構成と将来構成を混同しない

実施項目:

- 本書を正本にする
- [OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md) を追加する
- [SERVICENOW_INTEGRATION_PLAN.md](./SERVICENOW_INTEGRATION_PLAN.md) を追加する
- `PRESENTATION.md` と `TECHNICAL_SPECIFICATION.md` には要約のみ追加する

### Phase 1: 監視と運用イベント基盤

目的:

- 障害検知
- 可視化
- 重大度の統一
- 後続処理につながるイベント入口作り

追加するもの:

- CloudWatch アラーム拡充
  - ALB `HTTPCode_ELB_5XX_Count`
  - ALB `HTTPCode_Target_5XX_Count`
  - ALB `UnHealthyHostCount`
  - ALB `TargetResponseTime`
  - EC2 `StatusCheckFailed`
  - EC2 `CPUUtilization`
  - RDS `CPUUtilization`
  - RDS `FreeStorageSpace`
  - RDS `FreeableMemory`
  - RDS `DatabaseConnections`
- CloudWatch ダッシュボード
  - 可用性
  - レイテンシ
  - DB 健全性
  - エラー傾向
- 重大度ルール
  - P1: サービス停止、DB 接続不可、Unhealthy host
  - P2: 5xx 増加、応答悪化
  - P3: リソース逼迫予兆
- EventBridge でアラームイベントを集約

ServiceNow / ITOM 観点:

- Event Management の入口を作る
- 単なる通知ではなく、イベント分類を前提に設計する

### Phase 2: Lambda でイベント正規化

目的:

- AWS の監視イベントを、運用イベントとして扱える形にそろえる
- ServiceNow に渡しやすい payload を定義する

追加するもの:

- EventBridge から Lambda を起動
- Lambda で以下を付与
  - `severity`
  - `source`
  - `resource_type`
  - `resource_id`
  - `environment`
  - `summary`
  - `details_url`
  - `runbook_id`
  - `dedupe_key`
- 転送先候補
  - SNS
  - SQS
  - OpsCenter
  - ServiceNow Table API

ServiceNow / ITOM 観点:

- イベント正規化
- ノイズ低減
- correlation の準備

### Phase 3: Systems Manager による初動整備

目的:

- 障害対応を AWS 側でも体系化する

追加するもの:

- OpsCenter
- Session Manager
- Run Command
- Automation

代表 runbook:

- ALB 5xx 増加時の切り分け
- EC2 ヘルス異常時のログ採取と再起動判断
- RDS 接続数急増時の確認手順

ServiceNow / ITOM 観点:

- Incident だけでなく、Operations と Runbook まで見据えた設計

### Phase 4: AWS Backup と復旧演習

目的:

- 継続性と復旧性の考え方を強める

方針:

- 初期は RDS automated backup + PITR を正本にする
- 次段で AWS Backup を採用

追加候補:

- Backup vault
- Backup plan
- RDS バックアップの一元管理
- Restore testing
- Backup Audit Manager

ServiceNow / ITOM / ITIL 観点:

- Service Continuity
- 復旧性の検証
- 統制の可視化

### Phase 5: AWS Config による構成管理

目的:

- CMDB / Discovery に寄せた構成管理の土台を作る

追加するもの:

- AWS Config
- 主要リソースの recording
  - CloudFront
  - ALB
  - EC2
  - RDS
  - Security Groups
  - IAM Role
- 最小ルール
  - 過剰公開 SG
  - RDS public accessibility
  - 暗号化設定

ServiceNow / ITOM 観点:

- Configuration Management
- 構成変更の追跡

### Phase 6: ServiceNow PDI 連携

目的:

- AWS イベントを ServiceNow 側へ渡し、ITOM の流れを実演できるようにする

優先順:

1. `CloudWatch -> EventBridge -> Lambda -> ServiceNow Table API`
2. `CloudWatch Alarm -> OpsCenter -> AWS Service Management Connector`
3. `AWS Config -> ServiceNow CMDB`

最初にやる範囲:

- P1/P2 アラームのみ連携
- 片方向連携
- correlation id に dedupe key を使う

ServiceNow 側マッピング候補:

- `short_description`
- `description`
- `severity`
- `impact`
- `urgency`
- `source`
- `correlation_id`
- `configuration_item` または resource reference

### Phase 7: ITIL 観点の整理

取り込む考え方:

- Incident Management
- Event Management
- Change Enablement
- Problem Management
- Service Continuity

ドキュメントに落とすもの:

- 重大度ルール
- 起票ルール
- runbook
- 変更手順
- 復旧手順

---

## 4. 最初の 1〜2 週間でやること

最初の増分として推奨するセット:

- CloudWatch アラーム拡充
- CloudWatch ダッシュボード追加
- EventBridge + Lambda によるイベント正規化
- 運用 runbook 作成
- ServiceNow PDI 連携設計の明文化

このセットで得られるもの:

- 監視
- イベント管理
- 初動手順
- 将来の ServiceNow 連携の土台

---

## 5. 優先度

高:

- CloudWatch アラーム拡充
- EventBridge
- Lambda 正規化
- Runbook

中:

- OpsCenter
- Session Manager
- AWS Backup restore testing

後段:

- AWS Config
- CMDB 連携
- 双方向連携

---

## 6. 判断基準

- まずは低コストで実装しやすいものから始める
- 既存の AWS/Terraform 構成を壊さずに拡張できるものを優先する
- ServiceNow 側は最初から全部つなげず、イベント連携から始める
- 単なる機能追加ではなく、運用プロセスまで説明できるものを優先する

---

## 7. 関連資料

- [OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md)
- [SERVICENOW_INTEGRATION_PLAN.md](./SERVICENOW_INTEGRATION_PLAN.md)
- [TECHNICAL_SPECIFICATION.md](./TECHNICAL_SPECIFICATION.md)
- [TERRAFORM_ARCHITECTURE.md](./TERRAFORM_ARCHITECTURE.md)
