# 環境変数自動生成

ステータス: **完了**（2026-03-09）

---

## なぜやるか

- terraform apply 後に IP、DNS 名等が変わるたびに手動で .env を書き換えるのはミスの元
- 1 コマンドで Terraform output → .env ファイル生成を自動化

## 何をしたか

- `scripts/generate-env.sh` を作成
- Terraform output + AWS CLI + tfvars から全値を取得し .env を生成

## 詳細手順

[docs/guides/05-generate-env.md](../guides/05-generate-env.md)
