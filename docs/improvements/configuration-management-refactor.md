# 設定値管理の整理

ステータス: 予定
優先度: 中

---

## 前提資料

- [このアプリの設定値マップ](../guides/10-configuration-map.md)
- [SSM Parameter Store の全体像](../guides/09-ssm-overview.md)

読み方:

- 先に `10-configuration-map.md` で、設定値全体の地図と `SSM / settings / constants / local/test` の役割を把握する
- 次に `09-ssm-overview.md` で、SSM の保存先と取得フロー、`.env` 生成の流れを確認する
- そのうえで本タスクで、何を `settings` 化し、何を code 固定に残すかを整理する

---

## なぜやるか

- 設定値が `SSM`、`Django settings`、`constants.py`、`local/test` に分かれており、初心者や将来の保守者が把握しづらい
- 外だしすべき値と code 固定のままでよい値の境界を明確にしたい
- 「外だしできるものは全部外だし」ではなく、責務ごとに適切な置き場へ整理したい

---

## 何をするか

- 設定値を次の 3 種類に仕分けする
  - `環境依存値`
  - `運用調整値`
  - `仕様固定値`
- `settings` 化候補を抽出して、Django settings をアプリ設定の入口として整理する
- SSM に残す値を固定する
  - secret
  - 本番環境依存値
  - インフラ依存値
- code に残す値を固定する
  - ドメイン定義
  - 学年開始月ロジック
  - 仕様として固定すべき値
- ドキュメントと実装の対応関係を揃える

---

## 実装対象

### `settings` 化候補

- `EMAIL_TIMEOUT`
- `ADMINS`
- `ACCOUNT_EMAIL_VERIFICATION`
- `HealthThresholds.*`
- `NoteSettings.*`
- `DashboardSettings.*`

### code 固定対象

- `ConditionLevel`
- `GradeLevel`
- 学年開始月ロジック

---

## 注意事項

- 何でも SSM に寄せない
- 何でも settings に寄せない
- ドメイン定義を設定値化しない
- 本番設定と `local.py` / `test.py` の上書きを混同しない

---

## 期待効果

- 設定値の所在が追いやすくなる
- 本番で調整したい閾値を code 修正なしで変更しやすくなる
- 初心者が「どこを見ればよいか」を理解しやすくなる
- 将来の保守や改善タスクで設計判断がしやすくなる
