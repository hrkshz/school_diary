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
| 2 | インフラ再構築（terraform apply） | 完了 | - | [infrastructure-rebuild.md](./infrastructure-rebuild.md) |
| 3 | イベント正規化（Lambda） | 予定 | 高 | [event-normalization.md](./event-normalization.md) |
| 4 | ServiceNow PDI 連携 | 予定 | 高 | [servicenow-integration.md](./servicenow-integration.md) |
| 5 | 障害対応自動化（Systems Manager） | 後段 | 低 | [incident-response-automation.md](./incident-response-automation.md) |
| 6 | バックアップ・復旧検証 | 後段 | 低 | [backup-restore-testing.md](./backup-restore-testing.md) |
| 7 | 構成変更追跡（AWS Config） | 後段 | 低 | [configuration-tracking.md](./configuration-tracking.md) |
| 8 | ITIL プロセス整理 | 後段 | 低 | [itil-process-alignment.md](./itil-process-alignment.md) |

## DevOps / CI/CD

| # | 取り組み | ステータス | 優先度 | 詳細 |
|---|---------|----------|--------|------|
| 15 | GitHub Actions デプロイパイプライン（OIDC + ECR + SSM） | 完了 | - | [cicd-pipeline.md](./cicd-pipeline.md) |
| 16 | 環境変数自動生成（Terraform output → .env） | 完了 | - | [env-automation.md](./env-automation.md) |
| 17 | CI テスト自動化（pytest + Ruff + mypy） | 予定 | 高 | [ci-testing.md](./ci-testing.md) |
| 18 | ブランチ保護 + PR レビューフロー | 予定 | 中 | [branch-protection.md](./branch-protection.md) |
| 19 | Docker イメージのセキュリティスキャン | 予定 | 中 | [container-security.md](./container-security.md) |
| 20 | Terraform CI（plan の自動実行 + PR コメント） | 予定 | 中 | [terraform-ci.md](./terraform-ci.md) |
| 26 | CD 動線の一本化（Terraform / SSM / EC2 / GitHub Actions の責務固定） | 予定 | 中 | [cd-responsibility-separation.md](./cd-responsibility-separation.md) |

## SRE / 可観測性

| # | 取り組み | ステータス | 優先度 | 詳細 |
|---|---------|----------|--------|------|
| 21 | 構造化ログ + ログ集約（CloudWatch Logs Insights） | 予定 | 中 | [structured-logging.md](./structured-logging.md) |
| 22 | SLI/SLO の定義とエラーバジェット | 予定 | 中 | [sli-slo.md](./sli-slo.md) |
| 23 | 合成監視（外形監視） | 予定 | 低 | [synthetic-monitoring.md](./synthetic-monitoring.md) |
| 24 | インシデント対応の振り返り（Postmortem テンプレート） | 後段 | 低 | [postmortem-process.md](./postmortem-process.md) |

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
| 25 | 設定値管理の整理（SSM / settings / constants の責務分離） | 予定 | 中 | [configuration-management-refactor.md](./configuration-management-refactor.md) |

---

## 実施順序

```
完了: #1 監視基盤 → #2 インフラ構築 → #15 CI/CD → #16 環境変数自動化
  ↓
次: #17 CI テスト + #3 イベント正規化
  ↓
#4 ServiceNow 連携 + #9 EC2 夜間停止 + #11 コスト異常検知
  ↓
#18 ブランチ保護 + #19 コンテナセキュリティ + #20 Terraform CI + #26 CD 動線の一本化
  ↓
#21 構造化ログ + #22 SLI/SLO
  ↓
#10 メンテナンスページ + #5〜8, #14, #23〜25 は必要に応じて
```
