# AWS Architecture Documentation

## 概要

School Diary（連絡帳管理システム）の AWS インフラストラクチャ設計書です。
高可用性とコスト最適化のバランスを取った 3 層 Web アプリケーション構成です。

## アーキテクチャ概要

### 3 層 Web アプリケーション構成

```
インターネット
    ↓ (HTTPS)
CloudFront（CDN）
    ↓ (HTTP)
Application Load Balancer（ALB）
    ↓ (HTTP:8000)
EC2インスタンス（Django + Gunicorn）
    ↓ (PostgreSQL:5432)
RDS（PostgreSQL）
```

### 主要コンポーネント

| コンポーネント | 役割                              | 冗長化                |
| -------------- | --------------------------------- | --------------------- |
| **CloudFront** | CDN、静的ファイル配信、HTTPS 終端 | グローバル            |
| **ALB**        | ロードバランサー、ヘルスチェック  | Multi-AZ 対応可能     |
| **EC2**        | Django アプリケーション           | Auto Scaling 対応可能 |
| **RDS**        | PostgreSQL データベース           | Multi-AZ 対応可能     |
| **S3**         | 静的ファイル、メディアファイル    | 高耐久性              |
| **ECR**        | Docker イメージリポジトリ         | 高可用性              |
| **CloudWatch** | 監視・ログ                        | -                     |

### Terraform モジュール構成

本プロジェクトは 12 モジュールに分割された Terraform 構成を採用しています。

```
terraform/
├── modules/
│   ├── vpc/                  # VPC、サブネット、ルートテーブル
│   ├── security_groups/      # セキュリティグループ
│   ├── ec2/                  # EC2インスタンス
│   ├── rds/                  # RDS（PostgreSQL）
│   ├── alb/                  # Application Load Balancer
│   ├── cloudfront/           # CloudFront CDN
│   ├── s3/                   # S3バケット
│   ├── ecr/                  # ECR（Dockerイメージ）
│   ├── iam/                  # IAMロール・ポリシー
│   ├── ses/                  # SES（メール送信）
│   ├── cloudwatch/           # CloudWatch監視
│   └── cloudwatch_logs/      # CloudWatch Logs
├── environments/
│   └── production/
│       ├── main.tf           # メイン設定
│       ├── variables.tf      # 変数定義
│       ├── outputs.tf        # 出力定義
│       └── terraform.tfvars  # 変数値（Git管理外）
└── ARCHITECTURE.md           # 詳細ドキュメント（330行）
```

## 構成要素

### ネットワーク層（VPC）

#### VPC

- **CIDR**: 10.0.0.0/16
- **リージョン**: ap-northeast-1 (東京)
- **DNS**: 有効
- **S3 VPC Endpoint**: コスト削減のため Gateway 型 VPC エンドポイント使用

#### Availability Zones

- **AZ-1a**: ap-northeast-1a（メイン）
- **AZ-1c**: ap-northeast-1c（冗長化用）

#### Subnets

**Public Subnets**（インターネット接続可能）:

- Public Subnet 1: 10.0.1.0/24 (AZ-1a)
  - EC2 インスタンス
  - ALB（一部）
- Public Subnet 2: 10.0.11.0/24 (AZ-1c)
  - ALB（一部）

**Private Subnets**（インターネット接続不可）:

- Private Subnet 1: 10.0.2.0/24 (AZ-1a)
  - RDS Primary
- Private Subnet 2: 10.0.12.0/24 (AZ-1c)
  - RDS Standby（Multi-AZ 時）

### コンピューティング層

#### EC2 インスタンス

- **インスタンスタイプ**: t3.micro
- **OS**: Ubuntu 22.04 LTS
- **配置**: Public Subnet 1 (AZ-1a)
- **用途**: Django アプリケーションサーバー
- **ポート**: 8000（アプリケーション）
- **IAM ロール**: S3 アクセス権限付与
- **ストレージ**: 20GB gp2

#### セキュリティグループ（EC2）

- **SSH**: ポート 22（管理者 IP からのみ）
- **HTTP**: ポート 8000（ALB Security Group からのみ）
- **Egress**: 全許可

### ロードバランサー層

#### Application Load Balancer (ALB)

- **タイプ**: Application Load Balancer
- **配置**: Public Subnet 1 & 2（Multi-AZ）
- **リスナー**: HTTP (80)
- **ターゲット**: EC2:8000
- **ヘルスチェック**: /diary/health/

#### セキュリティグループ（ALB）

- **HTTP**: ポート 80（CloudFront Managed Prefix List からのみ）
- **HTTPS**: ポート 443（未設定、ALB リスナーは HTTP のみ）
- **Egress**: 全許可

**注**: CloudFront Managed Prefix List（pl-58a04531）を使用して CloudFront からのアクセスのみを許可。Prefix List には約 45 個の CloudFront IP アドレスが含まれており、これが 45 ルール相当としてカウントされる。

### データベース層

#### RDS PostgreSQL

- **エンジン**: PostgreSQL 16.10
- **インスタンスクラス**: db.t3.micro
- **ストレージ**: 20GB gp3（暗号化有効）
- **配置**: Private Subnet 1 & 2
- **Multi-AZ**: false（コスト最適化、本番環境では推奨: true）
- **バックアップ**: 7 日間保持
- **メンテナンスウィンドウ**: 月曜 04:00-05:00 JST
- **CloudWatch Logs**: postgresql, upgrade

#### セキュリティグループ（RDS）

- **PostgreSQL**: ポート 5432（EC2 セキュリティグループからのみ）

### CDN 層

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
- **ライフサイクル**: 90 日後に古いバージョン削除
- **VPC Endpoint**: Gateway 型エンドポイント経由でアクセス

### その他のサービス

#### SES (Simple Email Service)

- **用途**: アプリケーションからのメール送信
- **認証**: IAM ロール経由

#### ECR (Elastic Container Registry)

- **用途**: Docker イメージ保管（将来的なコンテナ化用）

#### CloudWatch

- **監視対象**:
  - EC2 メトリクス（CPU、メモリ、ディスク）
  - ALB メトリクス（リクエスト数、レイテンシ）
  - RDS メトリクス（接続数、CPU、ストレージ）
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

### Static/Media ファイルアクセス

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
3. **SSH 制限**: 管理者 IP からのみアクセス可能
4. **経路制限**: CloudFront → ALB → EC2 の経路のみアクセス可能
5. **CloudFront Managed Prefix List**: ALB へのアクセスを CloudFront のみに制限
6. **ALB 経由のみ**: EC2 への直接アクセスを完全遮断

### データセキュリティ

1. **暗号化**: RDS、S3 ともに暗号化有効
2. **バックアップ**: RDS 自動バックアップ（7 日保持）
3. **S3 バージョニング**: 誤削除対策

### アクセス制御

1. **IAM Role**: EC2 には S3 アクセス権限のみ付与
2. **S3 パブリックアクセスブロック**: 全て有効

## 高可用性設計

### Multi-AZ 構成

- **ALB**: 2 つの AZ に配置（自動フェイルオーバー）
- **RDS**: Single-AZ（コスト最適化、本番環境では推奨: Multi-AZ）

### スケーラビリティ

- **水平スケール**: ALB と Auto Scaling で対応可能（現在は手動）
- **垂直スケール**: EC2、RDS のインスタンスタイプ変更で対応
