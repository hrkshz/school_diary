# 構造化ログ + ログ集約

ステータス: 予定
優先度: 中

---

## なぜやるか

- 現在のログはテキストベースで、検索・集計が困難
- 構造化ログ（JSON）にすることで CloudWatch Logs Insights でクエリできる
- 障害時の原因特定を速くする

## 何をするか

- Django のログ出力を JSON フォーマットに変更（structlog または python-json-logger）
- リクエスト ID、ユーザー ID、処理時間などをログに自動付与
- CloudWatch Logs Insights でエラー集計、遅いリクエストの特定
- ダッシュボードにログベースのウィジェットを追加
