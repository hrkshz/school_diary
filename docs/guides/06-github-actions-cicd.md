# GitHub Actions CI/CD の構築

このドキュメントは、**CD をどう構築したか**を説明する導入ガイドです。
「今どう動いているか」の正本は [08-current-cd-flow.md](./08-current-cd-flow.md)、最短入口は [11-cd-canonical-flow.md](./11-cd-canonical-flow.md) を参照してください。

## なぜやるか

手動デプロイは:
- 手順が多く、間違えやすい
- 毎回 SSH + rsync + docker build が必要
- ローカルに Docker が必要（WSL2 環境では動かないこともある）

GitHub Actions で自動化すると:
- 対象ファイルの `git push` で本番 deploy を起動できる
- ビルドは GitHub のサーバーで行われる（ローカル環境不要）
- 履歴が残る（誰が、いつ、何をデプロイしたか）

## アーキテクチャ

```
git push (main)
  → GitHub Actions 起動
  → OIDC で AWS に認証（静的クレデンシャル不要）
  → Docker build → ECR に push
  → SSM Run Command で EC2 にデプロイ開始を指示
  → EC2 上の固定 deploy script が本番反映を実行
  → ヘルスチェックで確認
```

責務分担:

- Terraform: インフラと設定の正本
- SSM: 本番設定の保管庫
- EC2: 実行主体
- GitHub Actions: オーケストレーター

### なぜ OIDC 認証か（vs Access Key）

| 方式 | セキュリティ | 運用 |
|------|-----------|------|
| Access Key | 静的クレデンシャル。漏洩リスクあり。定期ローテーション必要 | GitHub Secrets に保存 |
| **OIDC** | 一時的なトークン。漏洩しても短時間で無効化 | IAM Role + 信頼ポリシー |

OIDC は AWS が推奨するモダンな方式。GitHub Actions が AWS に「自分は hrkshz/school_diary リポジトリの Actions です」と証明し、AWS が一時的な認証情報を返す。

### なぜ SSM Run Command か（vs SSH）

| 方式 | セキュリティ | 運用 |
|------|-----------|------|
| SSH | SSH 鍵を GitHub Secrets に保存。ポート 22 を開放 | 鍵管理が必要 |
| **SSM** | IAM ベースの認証。ポート開放不要 | AWS 管理。実行ログが CloudTrail に残る |

## 何をしたか

### 手順 1: Terraform で OIDC プロバイダ + IAM ロールを作成

`terraform/modules/github_actions/` モジュールを新規作成。

**OIDC プロバイダ:**

```hcl
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}
```

**IAM ロール（GitHub Actions 用）:**

```hcl
resource "aws_iam_role" "github_actions" {
  assume_role_policy = jsonencode({
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringLike = {
          "token.actions.githubusercontent.com:sub" = [
            "repo:hrkshz/school_diary:ref:refs/heads/main",
            "repo:hrkshz/school_diary:environment:production"
          ]
        }
      }
    }]
  })
}
```

**Condition の意味:** `hrkshz/school_diary` リポジトリの中でも、`main` ブランチ実行と `production` environment 実行だけがこのロールを使える。他のリポジトリや他ブランチの実行からは使えない。

**付与した権限:**
- ECR: イメージの push
- SSM: EC2 へのコマンド送信
- SSM: コマンド結果の取得

### 手順 2: EC2 に SSM 権限を追加

`terraform/modules/iam/main.tf` に追加:

```hcl
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
```

これにより EC2 上の SSM Agent が AWS と通信でき、Run Command を受け付けられる。

### 手順 3: GitHub Actions ワークフローの作成

`.github/workflows/deploy.yml`:

**トリガー:**
- `main` ブランチへの push（docs/ や terraform/ の変更は除外）
- 手動実行（workflow_dispatch）

**ジョブの流れ:**
1. ソースコードをチェックアウト
2. OIDC で AWS に認証
3. ECR にログイン
4. Docker イメージをビルド（コミット SHA + latest でタグ付け）
5. ECR に push
6. SSM Run Command で EC2 に deploy 開始を指示
7. EC2 上の `scripts/ssm-deploy.sh` が本番反映を実行
8. ヘルスチェックで確認

### 手順 5: GitHub Secrets の設定

GitHub リポジトリの Settings → Secrets and variables → Actions に以下を設定:

| Secret 名 | 値 | 取得方法 |
|-----------|---|---------|
| `AWS_ROLE_ARN` | GitHub Actions 用 IAM ロール ARN | `terraform output github_actions_role_arn` |
| `EC2_INSTANCE_ID` | EC2 インスタンス ID | `terraform output` または AWS コンソール |

また、Settings → Environments で `production` 環境を作成する。

### 手順 6: terraform apply

```bash
cd terraform/environments/production
terraform init    # 新モジュールの読み込み
terraform apply   # OIDC プロバイダ + IAM ロール + SSM 権限を作成
```

## デプロイの流れ（完成後）

```bash
# 1. コード変更をコミット
git add .
git commit -m "fix: something"

# 2. 対象ファイルを push
git push github main

# 3. GitHub Actions が自動でデプロイ
# → Actions タブで進捗を確認
```

補足:

- `docs/**`
- ルート直下の `*.md`
- `terraform/**`

だけの変更では deploy は起動しません。
- 最初の 1 回は `workflow_dispatch` で手動実行して成功ログを確認する運用が安全です。

## 確認方法

- GitHub → Actions タブでワークフローの実行状況を確認
- AWS コンソール → ECR でイメージが push されているか確認
- AWS コンソール → Systems Manager → Run Command で実行履歴を確認
- `https://<cloudfront-domain>/diary/health/` で 200 が返るか確認

## ブログで深掘りできるポイント

- GitHub Actions OIDC と AWS IAM の信頼関係の仕組み
- OIDC トークンの中身（JWT の claims）
- SSM Run Command vs SSH のセキュリティ比較
- Docker マルチステージビルドの最適化
- ECR のライフサイクルポリシー（古いイメージの自動削除）
- GitHub Environments と protection rules
