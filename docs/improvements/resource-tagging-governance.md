# リソースタグ監査

ステータス: 後段
優先度: 低

---

## なぜやるか

- タグベースのリソース管理（夜間停止等）の前提としてタグの統一が必要
- AWS Config の `required-tags` ルールで自動チェックできる
- ITIL の Configuration Management / Change Enablement の文脈で説明できる

## 何をするか

- 必須タグの定義（Project, Environment, ManagedBy, Severity 等）
- AWS Config ルールでタグ未設定リソースを検出
- 定期レポート

## 前提

- AWS Config（#7）の有効化が必要
- Config は有料のため、コスト対効果を考慮

## コスト

AWS Config の費用に含まれる（~$2/月）
