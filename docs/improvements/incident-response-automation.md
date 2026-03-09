# 障害対応自動化

ステータス: 後段
優先度: 低

---

## なぜやるか

- 障害対応を AWS 側で体系化する
- OpsCenter でインシデント管理、Session Manager でセキュアなアクセス
- Runbook と連動した初動自動化

## 何をするか

- OpsCenter 有効化
- Session Manager 設定（SSH 代替）
- Run Command / Automation で代表的な Runbook 実装
  - ALB 5xx 増加時の切り分け
  - EC2 ヘルス異常時のログ採取と再起動判断
  - RDS 接続数急増時の確認手順

## コスト

無料枠内（OpsCenter, Session Manager, Run Command は無料）
