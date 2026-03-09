# Continuous Improvement

運用品質とコスト最適化の継続的な改善に取り組んでいます。

作成日: 2026-03-09

---

## ステータス凡例

- **完了**: 実装済み
- **次**: 次に着手
- **予定**: 実施予定
- **確認要**: 対応要否の確認が必要
- **後段**: 必要になったら実施

---

## 監視・イベント管理

| # | 取り組み | ステータス | 優先度 | 詳細 |
|---|---------|----------|--------|------|
| 1 | アラーム重大度分類 + ダッシュボード整備 | 完了 | - | [monitoring-severity-dashboard.md](./monitoring-severity-dashboard.md) |
| 2 | インフラ再構築（terraform apply） | **次** | 高 | [infrastructure-rebuild.md](./infrastructure-rebuild.md) |
| 3 | イベント正規化（Lambda） | 予定 | 高 | [event-normalization.md](./event-normalization.md) |
| 4 | ServiceNow PDI 連携 | 予定 | 高 | [servicenow-integration.md](./servicenow-integration.md) |
| 5 | 障害対応自動化（Systems Manager） | 後段 | 低 | [incident-response-automation.md](./incident-response-automation.md) |
| 6 | バックアップ・復旧検証 | 後段 | 低 | [backup-restore-testing.md](./backup-restore-testing.md) |
| 7 | 構成変更追跡（AWS Config） | 後段 | 低 | [configuration-tracking.md](./configuration-tracking.md) |
| 8 | ITIL プロセス整理 | 後段 | 低 | [itil-process-alignment.md](./itil-process-alignment.md) |

## コスト最適化

| # | 取り組み | ステータス | 優先度 | 詳細 |
|---|---------|----------|--------|------|
| 9 | タグベース EC2 夜間自動停止 | 予定 | 中 | [scheduled-resource-control.md](./scheduled-resource-control.md) |
| 10 | メンテナンスページ切替による環境制御 | 予定 | 中 | [service-availability-control.md](./service-availability-control.md) |
| 11 | コスト異常検知 → ServiceNow 起票 | 予定 | 中 | [cost-anomaly-detection.md](./cost-anomaly-detection.md) |
| 12 | 暗号化キーの最適化 | 確認要 | 低 | [encryption-key-optimization.md](./encryption-key-optimization.md) |
| 13 | シークレット管理の最適化 | 確認要 | 低 | [secret-management-optimization.md](./secret-management-optimization.md) |

## ガバナンス

| # | 取り組み | ステータス | 優先度 | 詳細 |
|---|---------|----------|--------|------|
| 14 | リソースタグ監査 | 後段 | 低 | [resource-tagging-governance.md](./resource-tagging-governance.md) |

---

## 実施順序

```
#2 インフラ再構築
  ↓
#3 イベント正規化 + #9 EC2 夜間停止（Lambda 実装が共通）
  ↓
#4 ServiceNow 連携 + #11 コスト異常検知
  ↓
#10 メンテナンスページ切替
  ↓
#5〜8, #14 は必要に応じて
```
