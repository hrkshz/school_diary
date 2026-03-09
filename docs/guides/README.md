# 実装ガイド一覧

本番運用を見据えた AWS インフラの構築・運用改善の手順書です。
技術ブログの土台として、各ガイドは「なぜやるか → 何をしたか → どう動くか」の構成で書いています。

---

## ガイド一覧

### 監視基盤の構築

| # | ガイド | 概要 |
|---|-------|------|
| 1 | [CloudWatch アラームの重大度設計](./01-alarm-severity.md) | 既存アラームに P1/P2/P3 分類を追加し、運用判断の基準を作る |
| 2 | [CloudWatch ダッシュボードの構築](./02-cloudwatch-dashboards.md) | AWS コンソールで「今何が起きているか」を一目で把握できる画面を作る |
| 3 | [EventBridge によるイベント集約](./03-eventbridge.md) | アラーム → イベント集約の仕組みを作り、ServiceNow 連携の土台にする |

### コスト分析と最適化

| # | ガイド | 概要 |
|---|-------|------|
| 4 | [AWS コスト分析の実践](./04-cost-analysis.md) | 請求データからコストの原因を特定し、構造的に理解する |

### デプロイ自動化

| # | ガイド | 概要 |
|---|-------|------|
| 5 | [環境変数の自動生成](./05-generate-env.md) | Terraform output → .env ファイル生成を1コマンドで行う |
| 6 | [GitHub Actions CI/CD の構築](./06-github-actions-cicd.md) | OIDC 認証 + ECR + SSM によるモダンなデプロイパイプライン |
| 7 | [Terraform による全環境構築](./07-terraform-apply.md) | terraform apply で AWS 環境を一括構築する手順と注意点 |
| 8 | [現状の GitHub Actions CD フロー](./08-current-cd-flow.md) | 現在の本番デプロイが GitHub Actions から AWS までどう流れるかを時系列で整理 |
| 9 | [SSM Parameter Store の全体像](./09-ssm-overview.md) | SSM に何があり、誰がいつ取得して Django 起動までどうつながるかを初心者向けに整理 |
| 10 | [このアプリの設定値マップ](./10-configuration-map.md) | 設定値がどこにあり、何のためにあり、誰が読むかを本番中心に俯瞰する入口ガイド |

---

## 前提知識

- Terraform の基本（resource, module, variable, output）
- AWS の基本（EC2, RDS, ALB, CloudWatch）
- Docker の基本（build, push, compose）
- GitHub Actions の基本（workflow, job, step）
