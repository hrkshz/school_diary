# プレゼンテーション - 連絡帳管理システム

---

## プロジェクト概要

**連絡帳管理システム**は、中学校向けの生徒・担任間連絡管理Webアプリケーションです。生徒が毎日の体調・メンタル状態・振り返りを記録し、担任が確認してフィードバックを行います。Django + PostgreSQL + Dockerで構築し、AWS上でプロダクショングレードのインフラをTerraformで実現しました。

**開発期間**: 約62時間（MVP → MLP → MAP → QA）
**技術スタック**: Python 3.12 / Django 5.1 / PostgreSQL 16 / Docker / Terraform / AWS
**本番環境**: https://d2wk3j2pacp33b.cloudfront.net

---

## 課題1の工夫点

### 1. なぜPoCでTerraformを使ったか

多くの応募者はdocker-composeでローカル環境を動かすだけだと思いますが、私は**本番グレードのAWSインフラをTerraformで構築**しました。理由は以下の3点です。

#### 理由1: 評価者に「動くもの」を見せたい

採用担当者がGitLabのコードを見ても、実際に動いている画面を見ない限りシステムの価値は伝わりません。そこで、**本番環境（AWS）を構築し、URLを提供することで、評価者がすぐにアクセスして試せる**ようにしました。

- **本番URL**: https://d2wk3j2pacp33b.cloudfront.net
- **ログイン**: admin@example.com / password123
- **すぐに試せる**: テストアカウント280名（管理者1名、担任9名、生徒270名）

#### 理由2: 本番環境への移行を見据えた設計

PoCの多くは「動けばいい」で終わりますが、本番運用を考えると以下が必要です：

- **高可用性**: CloudFront + NLB + EC2 + RDS
- **監視**: CloudWatch Logs、CloudWatch Alarms
- **バックアップ**: RDS自動バックアップ（日次、保持期間7日）
- **セキュリティ**: セキュリティグループによる多層防御、SSL/TLS（ACM証明書）

これらを**Terraformで完全にIaC化**することで、「PoCで終わらせない」姿勢を示しました。

#### 理由3: インフラ自動化スキルの証明

現代のWebアプリケーション開発では、インフラの自動化スキルが必須です。Terraformを使うことで、以下のスキルを証明できます：

- IaCによるインフラ構築
- AWS Well-Architected Frameworkへの準拠
- モジュール化による再利用可能な設計
- 変更履歴のGit管理

---

### 2. Terraformによる完全なIaC化

#### 14モジュールに分割した再利用可能な設計

```
terraform/
├── modules/
│   ├── vpc/                  # VPC、サブネット、ルートテーブル
│   ├── security_groups/      # セキュリティグループ
│   ├── ec2/                  # EC2インスタンス
│   ├── rds/                  # RDS（PostgreSQL）
│   ├── nlb/                  # Network Load Balancer
│   ├── cloudfront/           # CloudFront CDN
│   ├── acm/                  # ACM証明書（SSL/TLS）
│   ├── cloudwatch/           # CloudWatch監視
│   ├── iam/                  # IAMロール・ポリシー
│   ├── route53/              # Route53（DNS）
│   └── ...                   # その他4モジュール
├── main.tf                   # メイン設定
├── variables.tf              # 変数定義
└── outputs.tf                # 出力定義
```

**各モジュールの責務**:
- **vpc**: VPC、パブリック/プライベートサブネット、インターネットゲートウェイ、NATゲートウェイ
- **security_groups**: ALB、EC2、RDS用のセキュリティグループ（最小権限の原則）
- **ec2**: Dockerがインストールされたアプリケーションサーバー
- **rds**: PostgreSQL 16データベース（プライベートサブネット配置）
- **nlb**: Network Load Balancer（SSL終端、ヘルスチェック）
- **cloudfront**: CDN（静的ファイル配信、HTTPS強制）
- **cloudwatch**: アプリケーションログ、エラーログ、メトリクス監視

**設計の特徴**:
- **再利用性**: 各モジュールは独立しており、他のプロジェクトでも使用可能
- **保守性**: 変更箇所を局所化、影響範囲を最小化
- **可読性**: モジュール名から責務が明確

---

### 3. AWS Well-Architected Frameworkへの準拠

AWSが推奨する5つの柱（運用の優秀性、セキュリティ、信頼性、パフォーマンス効率、コスト最適化）に準拠した設計を行いました。

#### 運用の優秀性

- **IaCによる自動化**: `terraform apply` で同一環境を構築可能
- **監視**: CloudWatch Logs、CloudWatch Alarms
- **ログ管理**: アプリケーションログ、エラーログを一元管理

#### セキュリティ

- **多層防御**: セキュリティグループによるファイアウォール（ALB、EC2、RDS）
- **最小権限の原則**: 必要最小限のポート開放（80, 443のみ）
- **データ保護**: RDSはプライベートサブネットに配置、EC2からのみアクセス可能
- **HTTPS強制**: CloudFrontでHTTPS強制、ACM証明書

#### 信頼性

- **自動バックアップ**: RDS日次バックアップ、保持期間7日
- **Multi-AZ対応可能**: RDSはMulti-AZ構成に変更可能（1行の設定変更）
- **ヘルスチェック**: NLBがEC2の健全性を監視、異常時は自動的にトラフィックを停止

#### パフォーマンス効率

- **CDN**: CloudFrontによる静的ファイル配信（グローバルエッジロケーション）
- **データベース最適化**: PostgreSQL INDEXによる高速検索
- **N+1問題対策**: Django ORMのselect_related/prefetch_relatedによる最適化

#### コスト最適化

- **リソースサイジング**: t3.smallインスタンス（月額約$15）
- **RDS**: db.t3.micro（月額約$15）
- **自動スケーリング対応可能**: Auto Scaling Groupに変更可能

---

### 4. 再現性への配慮

Terraformの最大の利点は「再現性」です。評価者が実際に動かして確認できるよう、以下を整備しました。

#### 再現手順（コピペで動く）

```bash
# 1. AWSクレデンシャルの設定
export AWS_ACCESS_KEY_ID="<your-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-secret-key>"
export AWS_DEFAULT_REGION="ap-northeast-1"

# 2. Terraformの初期化
cd terraform
terraform init

# 3. インフラの構築（約10分）
terraform apply

# 4. 出力情報の確認
terraform output
```

#### 期待される出力

```
cloudfront_domain = "d2wk3j2pacp33b.cloudfront.net"
ec2_public_ip = "54.xxx.xxx.xxx"
rds_endpoint = "school-diary.xxx.ap-northeast-1.rds.amazonaws.com"
```

#### 変更履歴のGit管理

Terraformファイルは全てGitで管理しており、以下の利点があります：

- **変更履歴**: いつ、誰が、何を変更したかが明確
- **ロールバック**: 問題があれば以前のバージョンに戻せる
- **レビュー**: Pull Requestによるコードレビュー

---

### 5. 本番グレードの証明

#### CloudFront + NLB + EC2 + RDS アーキテクチャ

```
インターネット
    ↓
CloudFront（CDN、HTTPS強制）
    ↓
Network Load Balancer（SSL終端、ヘルスチェック）
    ↓
EC2（Django + Gunicorn）
    ↓
RDS（PostgreSQL、プライベートサブネット）
```

**なぜこの構成か**:

| コンポーネント | 理由 |
|-------------|------|
| **CloudFront** | グローバルCDN、静的ファイル配信の高速化、HTTPS強制 |
| **NLB** | L4ロードバランサー、ヘルスチェック、SSL終端 |
| **EC2** | Dockerコンテナ実行、スケーラブル |
| **RDS** | マネージドPostgreSQL、自動バックアップ、Multi-AZ対応可能 |

#### Multi-AZ対応可能な構成

現在はシングルAZ構成ですが、以下の設定変更でMulti-AZ対応可能です：

```hcl
# terraform/modules/rds/main.tf
resource "aws_db_instance" "this" {
  # ...
  multi_az = true  # この1行を追加するだけ
}
```

#### CloudWatch監視

アプリケーションログ、エラーログ、メトリクスを一元管理：

- **CloudWatch Logs**: アプリケーションログ、エラーログ
- **CloudWatch Alarms**: CPU使用率、メモリ使用率、RDS接続数
- **ダッシュボード**: 各種メトリクスを可視化

---

### 6. なぜAWSを選んだか

#### 技術選定の背景

インターン先はAzure環境だが、私はAWS実務経験5年、Azure未経験。課題に技術指定がなかったため、AWSで実装した。

#### 判断理由

62時間という制約の中で本番グレードのインフラを構築するため、5年の経験を活かす判断をした。結果、CloudFront + NLB + EC2 + RDS、Terraform 14モジュール、Well-Architected Framework準拠を実現できた。

Azure未経験で実装した場合、品質が下がるリスクがあった。時間制約とクオリティを両立するため、AWS選択は合理的だと考える。

#### クラウド原理原則の理解

実装したアーキテクチャは、AWS固有の知識ではなく、クラウド共通の原理原則に基づいている。

**層構造**:
- CDN層: グローバルエッジロケーション、静的ファイル配信
- ロードバランサー層: SSL終端、ヘルスチェック
- コンピューティング層: アプリケーション実行
- データベース層: マネージドDB、自動バックアップ

この構造はAzure/GCP/オンプレミスでも同じ。

#### AWS → Azure 移行マッピング

| AWS | Azure | 役割 |
|-----|-------|------|
| CloudFront | Azure Front Door | CDN、HTTPS終端 |
| Network Load Balancer | Azure Load Balancer | L4ロードバランサー |
| EC2 | Azure Virtual Machines | コンピューティング |
| RDS (PostgreSQL) | Azure Database for PostgreSQL | マネージドDB |
| Terraform | Terraform (Azure Provider) / Bicep | IaC |
| CloudWatch | Azure Monitor | 監視・ログ |

#### 入社後の対応

入社前にAzure Fundamentalsを学習し、入社後1ヶ月でAzure環境に適応する。クラウドアーキテクチャの原理原則を理解しているため、ツールの違いは問題にならない。

---

## 課題2のプレゼンテーション

### 実装の背景

担任教師が毎日30名以上の生徒の連絡帳を確認するのは大変です。そこで、**Inbox Pattern（優先度別分類）** と **早期警告システム** を実装しました。

### Inbox Pattern: 7カテゴリ分類

担任ダッシュボードでは、生徒を優先度順に7つのカテゴリに自動分類します。

| カテゴリ | 優先度 | 説明 |
|---------|--------|------|
| **P0: 重要** | 最高 | 3日連続メンタル低下、メンタル★1（即時対応） |
| **P1: 要注意** | 高 | メンタル★2（注意が必要） |
| **P1.5: 要対応タスク** | 高 | 既読済みで対応記録あり（保護者連絡、個別面談など） |
| **P2-1: 未提出** | 中 | 今日の連絡帳未提出 |
| **P2-2: 未読** | 中 | 提出済みだが未確認 |
| **P2-3: 反応待ち** | 低 | 既読済みだが反応未選択 |
| **P3: 完了済み** | 低 | 既読・反応済み |

**実装方法**:
- `alert_service.py`で分類ロジックを実装（TDD、9テスト全合格）
- N+1問題対策（select_related/prefetch_relatedによる最適化）

### 早期警告システム

**3日連続メンタル低下検知**:
- 過去3日間のメンタル状態を分析
- 連続して低下している場合は「P0: 重要」に分類
- 担任が見逃さないようカード上部に表示

**メンタル★1検知**:
- メンタル★1（とても悪い）の生徒は即座に「P0: 重要」に分類
- 即時対応が必要な生徒を担任が一目で把握

### UIの工夫

#### 3-tier card UI（Critical/High/Normal分類）

カードの色で優先度を視覚的に表現：

| 優先度 | 色 | 対象カテゴリ |
|--------|---|------------|
| **Critical** | 赤 | P0: 重要 |
| **High** | 黄色 | P1: 要注意、P1.5: 要対応タスク |
| **Normal** | 白 | P2-1, P2-2, P2-3, P3 |

#### Inline history integration（3日推移表示）

各カードに過去3日分の体調・メンタル推移を表示：

```
[履歴 3日間] 体調: ★4 → ★3 → ★2 / メンタル: ★3 → ★2 → ★1
```

担任は推移を見て「メンタルが下がり続けている」ことに気づけます。

---

## 技術スタック

### バックエンド

- **Python 3.12**: 最新の安定版
- **Django 5.1**: Webフレームワーク
- **PostgreSQL 16**: リレーショナルデータベース
- **Gunicorn**: WSGIサーバー（本番環境）

### フロントエンド

- **Bootstrap 5**: CSSフレームワーク
- **Django Templates**: サーバーサイドレンダリング
- **AJAX**: 既読処理、出席記録の非同期通信

### インフラ

- **Docker**: コンテナ化
- **Docker Compose**: 開発環境
- **Terraform**: IaC
- **AWS**: CloudFront, NLB, EC2, RDS, CloudWatch

### 開発ツール

- **uv**: 依存関係管理
- **Ruff**: Linter / Formatter
- **pytest**: テストフレームワーク（150+ テスト）
- **mypy**: 型チェック

---

## 開発プロセス

### Phase別アプローチ

| Phase | 期間 | 目標 | 成果 |
|-------|------|------|------|
| **MVP** | 11.4h | 60点、基本機能 | 連絡帳作成・確認、認証 |
| **MLP** | 26.7h | 75点、UI改善 | 担任ダッシュボード、既読処理 |
| **MAP** | 22.75h | 85点、高度機能 | Inbox Pattern、早期警告システム |
| **QA** | 1h | 90点、品質保証 | バグ修正、As-Built仕様書 |
| **AWS** | 0.5h | 95点、本番環境 | Terraform、AWS構築 |

### 品質管理

- **テスト**: pytest（150+ テスト）、カバレッジ90%以上
- **Lint**: Ruff（Django標準設定）、セキュリティ・バグリスクは全て解決済み
- **型チェック**: mypy（strict モード）
- **セキュリティ**: Checkov（IaC静的解析）

---

## 成果・達成したこと

### 機能面

✅ 生徒向け機能（連絡帳作成・編集・履歴）
✅ 担任向け機能（Inbox Pattern、既読処理、担任メモ、出席記録）
✅ 学年主任向け機能（学年統計）
✅ 校長/教頭向け機能（学校統計）
✅ 管理者向け機能（Django管理画面）

### インフラ面

✅ Terraformによる完全なIaC化（14モジュール）
✅ AWS本番環境構築（CloudFront + NLB + EC2 + RDS）
✅ CloudWatch監視、RDS自動バックアップ
✅ セキュリティグループによる多層防御
✅ 再現性（terraform applyで同一環境構築可能）

### 品質面

✅ 150+ テスト（pytest）、カバレッジ90%以上
✅ Ruff（Lint）、mypy（型チェック）、Checkov（IaC静的解析）
✅ As-Built仕様書作成（実装と100%一致する仕様書）
✅ ドキュメント整備（USER_MANUAL.md、ER_DIAGRAM.md、DEPLOYMENT.md）

---

## 課題・インターンの感想

### 学び

#### 1. TDD

Inbox Pattern実装時、TDD（テスト駆動開発）を本格的に実践した。先にテストを書くことで、仕様が明確になり、リファクタリング時の安心感が得られた。バグの早期発見にもつながった。

#### 2. Terraformによるインフラ構築

PoCでTerraformを使うことで、IaCの利点（再現性・保守性）を実感した。モジュール化により再利用性が向上し、AWS Well-Architected Frameworkに基づいた設計を実現できた。

#### 3. ユーザー視点の設計

担任教師が毎日30名以上の生徒の連絡帳を確認する大変さを想像し、Inbox Patternを実装した。技術だけでなく、ユーザーの課題を理解して解決することが重要だと感じた。

### 課題

#### 1. テストカバレッジの向上

現在のカバレッジは90%以上だが、100%を目指してエッジケースのテストを追加する必要がある。

#### 2. パフォーマンス最適化

N+1問題は解決したが、さらなる最適化（キャッシュ、インデックスチューニング）の余地がある。

#### 3. CI/CDパイプラインの整備

現在は手動デプロイだが、GitHub Actionsによる自動テスト・自動デプロイを整備したい。

### インターンへの意気込み

今回の課題を通じて、PoCで終わらせない姿勢の重要性を学んだ。インターンでは以下に取り組みたい：

1. 本番運用を見据えた開発
2. ユーザー視点の設計
3. チーム開発スキルの向上（コードレビュー、ペアプログラミング）

---

## まとめ

連絡帳管理システムは、**PoCで終わらせない姿勢**で開発しました。

- **課題1**: Terraformによる完全なIaC化、AWS本番環境構築
- **課題2**: Inbox Pattern、早期警告システム
- **品質**: 150+ テスト、カバレッジ90%以上、As-Built仕様書

評価者がすぐに試せるよう、以下を整備しました：

- **本番環境**: https://d2wk3j2pacp33b.cloudfront.net
- **テストアカウント**: admin@example.com / password123
- **ドキュメント**: USER_MANUAL.md、ER_DIAGRAM.md、DEPLOYMENT.md、TEST_ACCOUNTS.md

**再現性**: `terraform apply` で同一環境を構築可能
