# AWS Architecture Documentation

## 概要

School Diary（連絡帳管理システム）のAWSインフラストラクチャ設計書です。
高可用性とコスト最適化のバランスを取った3層Webアプリケーション構成です。

## アーキテクチャ図

構成図: `aws-architecture.drawio`

draw.ioで開いて閲覧・編集が可能です。
- オンライン: https://app.diagrams.net/
- ローカル: draw.ioデスクトップアプリ

## 構成要素

### ネットワーク層（VPC）

#### VPC
- **CIDR**: 10.0.0.0/16
- **リージョン**: ap-northeast-1 (東京)
- **DNS**: 有効
- **S3 VPC Endpoint**: コスト削減のためGateway型VPCエンドポイント使用

#### Availability Zones
- **AZ-1a**: ap-northeast-1a（メイン）
- **AZ-1c**: ap-northeast-1c（冗長化用）

#### Subnets

**Public Subnets**（インターネット接続可能）:
- Public Subnet 1: 10.0.1.0/24 (AZ-1a)
  - EC2インスタンス
  - ALB（一部）
- Public Subnet 2: 10.0.11.0/24 (AZ-1c)
  - ALB（一部）

**Private Subnets**（インターネット接続不可）:
- Private Subnet 1: 10.0.2.0/24 (AZ-1a)
  - RDS Primary
- Private Subnet 2: 10.0.12.0/24 (AZ-1c)
  - RDS Standby（Multi-AZ時）

### コンピューティング層

#### EC2インスタンス
- **インスタンスタイプ**: t3.micro
- **OS**: Ubuntu 22.04 LTS
- **配置**: Public Subnet 1 (AZ-1a)
- **用途**: Djangoアプリケーションサーバー
- **ポート**: 8000（アプリケーション）
- **IAMロール**: S3アクセス権限付与
- **ストレージ**: 20GB gp2

#### セキュリティグループ（EC2）
- **SSH**: ポート22（管理者IPからのみ）
- **HTTP**: ポート8000（ALB Security Groupからのみ）
- **Egress**: 全許可

### ロードバランサー層

#### Application Load Balancer (ALB)
- **タイプ**: Application Load Balancer
- **配置**: Public Subnet 1 & 2（Multi-AZ）
- **リスナー**: HTTP (80)
- **ターゲット**: EC2:8000
- **ヘルスチェック**: /diary/health/

#### セキュリティグループ（ALB）
- **HTTP**: ポート80（CloudFront Managed Prefix Listからのみ）
- **HTTPS**: ポート443（未設定、ALBリスナーはHTTPのみ）
- **Egress**: 全許可

**注**: CloudFront Managed Prefix List（pl-58a04531）を使用してCloudFrontからのアクセスのみを許可。Prefix Listには約45個のCloudFront IPアドレスが含まれており、これが45ルール相当としてカウントされる。

### データベース層

#### RDS PostgreSQL
- **エンジン**: PostgreSQL 16.10
- **インスタンスクラス**: db.t3.micro
- **ストレージ**: 20GB gp3（暗号化有効）
- **配置**: Private Subnet 1 & 2
- **Multi-AZ**: false（コスト最適化、本番環境では推奨: true）
- **バックアップ**: 7日間保持
- **メンテナンスウィンドウ**: 月曜 04:00-05:00 JST
- **CloudWatch Logs**: postgresql, upgrade

#### セキュリティグループ（RDS）
- **PostgreSQL**: ポート5432（EC2セキュリティグループからのみ）

### CDN層

#### CloudFront
- **オリジン**: ALB
- **プロトコル**: HTTP -> HTTPS リダイレクト
- **キャッシュポリシー**: CachingDisabled（動的コンテンツ）
- **圧縮**: 有効
- **証明書**: CloudFront デフォルト証明書

### ストレージ層

#### S3 Bucket
- **用途**: Static files、Media files
- **バージョニング**: 有効
- **暗号化**: SSE-S3（AES256）
- **パブリックアクセス**: ブロック
- **ライフサイクル**: 90日後に古いバージョン削除
- **VPC Endpoint**: Gateway型エンドポイント経由でアクセス

### その他のサービス

#### SES (Simple Email Service)
- **用途**: アプリケーションからのメール送信
- **認証**: IAMロール経由

#### ECR (Elastic Container Registry)
- **用途**: Dockerイメージ保管（将来的なコンテナ化用）

#### CloudWatch
- **監視対象**:
  - EC2メトリクス（CPU、メモリ、ディスク）
  - ALBメトリクス（リクエスト数、レイテンシ）
  - RDSメトリクス（接続数、CPU、ストレージ）
- **アラート**: 指定メールアドレスに通知

## トラフィックフロー

### ユーザーアクセスの流れ

```
Internet User
    ↓ (HTTPS)
CloudFront (CDN)
    ↓ (HTTP)
Application Load Balancer
    ↓ (HTTP:8000)
EC2 Instance (Django)
    ↓ (PostgreSQL:5432)
RDS PostgreSQL
```

### Static/Mediaファイルアクセス

```
EC2 Instance
    ↓ (S3 API via VPC Endpoint)
S3 VPC Endpoint (Gateway)
    ↓
S3 Bucket
```

### メール送信

```
EC2 Instance
    ↓ (SMTP/API)
SES
    ↓
Email Recipients
```

## セキュリティ対策

### ネットワークセキュリティ
1. **Private Subnet**: データベースはインターネットから隔離
2. **Security Groups**: 最小権限の原則
3. **SSH制限**: 管理者IPからのみアクセス可能
4. **経路制限**: CloudFront → ALB → EC2の経路のみアクセス可能
5. **CloudFront Managed Prefix List**: ALBへのアクセスをCloudFrontのみに制限
6. **ALB経由のみ**: EC2への直接アクセスを完全遮断

### データセキュリティ
1. **暗号化**: RDS、S3ともに暗号化有効
2. **バックアップ**: RDS自動バックアップ（7日保持）
3. **S3バージョニング**: 誤削除対策

### アクセス制御
1. **IAM Role**: EC2にはS3アクセス権限のみ付与
2. **S3パブリックアクセスブロック**: 全て有効

## 高可用性設計

### Multi-AZ構成
- **ALB**: 2つのAZに配置（自動フェイルオーバー）
- **RDS**: Single-AZ（コスト最適化、本番環境では推奨: Multi-AZ）

### スケーラビリティ
- **水平スケール**: ALBとAuto Scalingで対応可能（現在は手動）
- **垂直スケール**: EC2、RDSのインスタンスタイプ変更で対応

## PoCステージのセキュリティ判断

### 実装済み対策（無料）
1. **経路制限**: CloudFront → ALB → EC2の経路のみアクセス可能
2. **HTTPS保護**: User → CloudFront間は暗号化（CloudFrontデフォルト証明書）
3. **データベース保護**: RDSはPrivate Subnet、EC2からのみアクセス
4. **CloudWatch監視**: 基本メトリクス監視

### PoCステージで許容するリスク（コスト優先）
1. **CloudFront → ALB間HTTP**: AWS内部ネットワーク通信、傍受リスク極小
2. **WAF未実装**: アプリケーション層対策で補完（Django標準機能）
3. **RDS Single-AZ**: バックアップで対応、ダウンタイム許容
4. **EC2 Public Subnet**: NAT Gateway不要、コスト削減

### 技術的制約と対応
1. **ALB HTTPS未設定**:
   - カスタムドメイン + ACM証明書が必要（年$12〜）
   - CloudFront Managed Prefix Listは45エントリ = 45ルール相当
   - ALB Security Group上限60ルールに対して、HTTP（45）+ HTTPS（45）= 90ルールで超過
   - 現在ALBリスナーはHTTPのみなので影響なし

### サービスイン時に必須の対策（追加コスト）
1. **カスタムドメイン + ACM**: End-to-End HTTPS（年$12〜）
2. **WAF**: OWASP Top 10対策（月$5-10）
3. **NAT Gateway + EC2移動**: Private Subnet化（月$32）
4. **RDS Multi-AZ**: 自動フェイルオーバー（月+$15）
5. **CloudTrail**: API監査ログ（無料、S3ストレージのみ月$1-2）

## コスト最適化

### 無料枠活用
- **EC2**: t3.micro（一部無料枠）
- **RDS**: db.t3.micro、Single-AZ
- **S3**: ライフサイクルポリシーで古いバージョン削除
- **CloudWatch**: 基本監視（5分間隔）

### コスト削減施策
1. **S3 VPC Endpoint**: データ転送料削減
2. **Single-AZ RDS**: Multi-AZよりコスト50%削減
3. **CloudFront**: Origin側の負荷軽減

## 運用管理

### モニタリング
- **CloudWatch**: 自動メトリクス収集
- **RDS Enhanced Monitoring**: データベースOS詳細メトリクス
- **ALB Access Logs**: アクセスログ（オプション）

### バックアップ
- **RDS**: 自動バックアップ（7日保持）
- **S3**: バージョニング有効

### メンテナンス
- **RDS**: 月曜 04:00-05:00（自動メンテナンスウィンドウ）
- **EC2**: 手動パッチ適用

## デプロイ手順

### 前提条件
- AWSアカウント
- Terraform ≥ 1.0
- AWS CLI設定済み

### 初期デプロイ

```bash
cd terraform/environments/production

# 変数ファイルの設定
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars  # 環境に応じて編集

# Terraform初期化
terraform init

# プラン確認
terraform plan -out=tfplan

# デプロイ実行
terraform apply tfplan
```

### 環境変数設定

EC2にSSHでログインし、環境変数を設定：

```bash
# .envs/.production/.django
# .envs/.production/.postgres
```

### アプリケーションデプロイ

```bash
# Docker Composeでアプリケーション起動
docker compose -f docker-compose.production.yml up -d

# マイグレーション実行
docker compose -f docker-compose.production.yml exec django python manage.py migrate

# 静的ファイル収集
docker compose -f docker-compose.production.yml exec django python manage.py collectstatic --noinput
```

## 今後の改善案

### 高可用性向上
1. **RDS Multi-AZ化**: ダウンタイム最小化
2. **Auto Scaling**: トラフィック増加時の自動スケール
3. **ECS/Fargate**: コンテナ化による運用効率化

### セキュリティ強化
1. **WAF導入**: SQLインジェクション、XSS対策
2. **カスタムドメイン**: Route 53 + ACM証明書
3. **Secrets Manager**: 認証情報の安全な管理
4. **GuardDuty**: 脅威検知

### 監視・運用
1. **X-Ray**: 分散トレーシング
2. **SNS**: アラート通知の拡充
3. **Systems Manager**: パッチ管理自動化
4. **CloudTrail**: API監査ログ

### コスト最適化
1. **Reserved Instances**: 長期利用によるコスト削減
2. **Savings Plans**: 柔軟な割引プラン
3. **S3 Intelligent-Tiering**: アクセス頻度に応じた自動階層化

## 参考資料

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Django on AWS Best Practices](https://docs.djangoproject.com/en/stable/howto/deployment/)

---

**作成日**: 2025-10-29
**最終更新**: 2025-10-29（Security Group経路制限実装、PoCステージ判断追加）
**バージョン**: 1.1
**管理者**: hirok
