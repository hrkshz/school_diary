# メンテナンスページ切替による環境制御

ステータス: 予定
優先度: 中

---

## なぜやるか

- 環境停止時（terraform destroy）に CloudFront の URL をそのまま維持したい
- メンテナンス中でも「ページが表示される」状態を保てる
- CloudFront + S3 は実質無料なので、常時残しておける

## 何をするか

- S3 にメンテナンスページ（静的 HTML）を配置
- Terraform 変数 `service_active`（true/false）で制御
  - `true`: CloudFront オリジン = ALB（通常稼働）
  - `false`: CloudFront オリジン = S3（メンテページ）
- ALB/EC2/RDS は `count` でリソース作成を制御

## 注意事項

- 既存モジュールに `count` を入れる改修が必要（変更量は中程度）
- CloudFront のディストリビューションは削除しない（ドメイン名が変わるため）

## コスト

- CloudFront + S3: 無料枠内
- 停止時は有料リソース（ALB/EC2/RDS）が存在しないため $0
