# Terraform CI（plan 自動実行 + PR コメント）

ステータス: 予定
優先度: 中

---

## なぜやるか

- Terraform の変更を PR で出したとき、plan 結果を自動で確認したい
- 「何が変わるか」を PR 上で確認してからマージできる
- インフラ変更のレビュープロセスを確立する

## 何をするか

- `.github/workflows/terraform.yml` を作成
- `terraform/` 配下の変更がある PR で自動実行
- `terraform plan` の結果を PR コメントに投稿
- Checkov によるセキュリティスキャンも実行
