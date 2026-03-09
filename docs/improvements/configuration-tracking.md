# 構成変更追跡

ステータス: 後段
優先度: 低

---

## なぜやるか

- CMDB / Discovery に寄せた構成管理の土台を作る
- 構成変更の追跡と、セキュリティルールの自動チェック

## 何をするか

- AWS Config 有効化
- 主要リソースの recording（CloudFront, ALB, EC2, RDS, SG, IAM Role）
- 最小ルール（過剰公開 SG、RDS public accessibility、暗号化設定）

## コスト

有料（Config recorder: ~$2/月 + ルール評価）
