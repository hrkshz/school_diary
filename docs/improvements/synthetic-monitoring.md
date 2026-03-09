# 合成監視（外形監視）

ステータス: 予定
優先度: 低

---

## なぜやるか

- CloudWatch アラームは AWS 内部のメトリクスを見ている
- ユーザー視点で「サイトが見えるか」を定期的に確認する仕組みがない
- 外部からの疎通確認で、DNS 障害や CloudFront 障害も検知できる

## 何をするか

- CloudWatch Synthetics Canary（Lambda ベースの外形監視）
- 定期的に CloudFront URL にアクセスし、HTTP 200 を確認
- 失敗時にアラーム → EventBridge → SNS 通知
