# ServiceNow PDI 連携

ステータス: 予定
優先度: 高

---

## なぜやるか

- ポートフォリオの最大のアピールポイント
- AWS の監視イベントを ServiceNow に自動起票する E2E フローを実演できる
- ITOM / Event Management の実践的理解を示せる

## 何をするか

- Lambda から ServiceNow PDI の Table API に POST
- P1/P2 アラームのみ連携（P3 は AWS 側で保持）
- dedupe_key で重複起票を防止

## ServiceNow 側マッピング

- `short_description`: 監視イベント要約
- `description`: 詳細
- `severity` / `impact` / `urgency`: AWS 側 severity から変換
- `source`: AWS
- `correlation_id`: dedupe_key

## 前提

- Phase 2（Lambda 正規化）が完了していること
- ServiceNow PDI インスタンスが利用可能であること

## コスト

無料（Lambda 無料枠 + ServiceNow PDI は無料）
