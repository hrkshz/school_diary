# CI テスト自動化

ステータス: 予定
優先度: 高

---

## なぜやるか

- PR やプッシュ時にテストが自動で走り、壊れたコードがデプロイされるのを防ぐ
- Ruff（linter）、mypy（型チェック）、pytest（ユニットテスト）を CI で実行
- コード品質の基準を自動で担保する

## 何をするか

- `.github/workflows/test.yml` を作成
- PR 作成時 + main ブランチ push 時にテストを実行
- pytest、Ruff、mypy を並列実行
- テスト結果を PR コメントに表示
