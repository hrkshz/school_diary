# Git ブランチ運用ルール（1枚）

対象: このリポジトリ全体（GitLab / main保護）
目的: 変更を安全・一貫・可視化して進めるための最小ルール

## TL;DR（最短手順）
1) mainから作業ブランチを切る（例: feature/login-form）
2) 変更して小さくコミット（Conventional Commits推奨）
3) ブランチをpush → GitLabでMR作成 → レビュー → Squash & Merge
4) マージ後は作業ブランチを削除

## ブランチ種別と命名
- main
  - 保護ブランチ。直接push禁止。MR経由のみ更新
  - 安定版（リリースの基点）。タグ付けはここで行う
- feature/<短い説明> … 新機能（例: feature/login-form）
- fix/<短い説明> … 不具合修正（例: fix/auth-refresh)
- hotfix/<短い説明> … 緊急修正（例: hotfix/production-500）
- chore/<短い説明> … 整備・依存更新（例: chore/update-deps）
- docs/<短い説明> … 文書のみ（例: docs/git-rules）

命名ルール:
- 英小文字・数字・ハイフン（-）・スラッシュ（/）のみ。空白・全角・特殊記号は不可
- 具体・簡潔（3〜5語目安）。例: feature/user-invite

## コミットメッセージ（Conventional Commits）
- 形式: `type(scope): 要約` 例: `feat(auth): add refresh token`
- よく使うtype: feat, fix, docs, chore, refactor, test, perf, build, ci, revert
- 要約は50文字目安、本文は72桁折返し
- Issue連携: `Refs #123` / 自動クローズ: `Closes #123`

## MR（マージリクエスト）ルール
- 1MR=1トピック（小さく早く）
- 説明には「変更点/理由/テスト方法/影響範囲」を記載
- レビュー1名以上（設定に従う）。Draft MRで早期共有も可
- マージ時は Squash 推奨。mainへ直接pushは不可

## 典型フロー（コマンド例）
git switch main && git pull --ff-only git switch -c feature/scope-summary

作業 → 変更
git add . git commit -m "feat(scope): brief summary" git push -u origin feature/scope-summary

GitLabでMR作成 → レビュー → Squash & Merge

## Do / Don't
- Do: 小さいMR、明確な命名、要約の質、関連Issue紐付け
- Don't: mainへ直接push、巨大MR、目的混在コミット

## トラブル時のヒント
- mainにpushできない → 仕様。作業ブランチ→MR経由
- リモートURLが違う/無い → `git remote -v` で確認、`git remote set-url origin ...`
- ブランチ名ミス → リネーム: `git branch -m old new`

（最終更新: 初版）
