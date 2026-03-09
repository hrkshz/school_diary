# バックアップ・復旧検証

ステータス: 後段
優先度: 低

---

## なぜやるか

- Service Continuity / 復旧性の設計を示す
- 現状は RDS automated backup（7 日保持）のみ
- AWS Backup で一元管理し、復旧テストの仕組みを作る

## 何をするか

- AWS Backup vault / plan 作成
- RDS バックアップの一元管理
- Restore testing
- Backup Audit Manager（オプション）

## コスト

要確認（バックアップストレージ量による）
