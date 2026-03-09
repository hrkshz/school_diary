# タグベース EC2 夜間自動停止

ステータス: 予定
優先度: 中

---

## なぜやるか

- パブリック IPv4 課金は EC2 稼働中も停止中（IP 解放時）も発生する
- EC2 停止で IP が解放され、夜間のIP 課金を削減できる（~$1.20/月）
- 金額より「タグベースでリソースライフサイクルを管理する仕組み」としてのアピール価値が高い
- ITOM / 運用自動化の実績として説明できる

## 何をするか

- EC2 に `AutoStop: 20:00`, `AutoStart: 07:00` タグを付与
- EventBridge Scheduler で定時起動
- Lambda でタグを読み取り、EC2 を stop/start

## Terraform で追加するリソース

- `aws_lambda_function`（EC2 stop/start）
- `aws_iam_role`（Lambda → EC2 操作権限）
- `aws_scheduler_schedule`（EventBridge Scheduler × 2）

## コスト

- 削減効果: ~$1.20/月（EC2 IP 課金の 1/3）
- 実装コスト: 無料枠内

## 備考

- Phase 2 Lambda と実装パターンが共通（同時実装推奨）
- ALB は停止機能がないため対象外
