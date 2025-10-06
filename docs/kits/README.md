# 📦 kits パッケージ ドキュメント

> **このドキュメントの目的**
>
> school_diaryの`kits`パッケージ全体を初心者でも理解できるように、丁寧に解説します。
> Web開発の知識がなくても、実装の意図・手順・使い方をトレースできることを目指しています。

**最終更新**: 2025-10-05

---

## 🎯 kitsパッケージとは？

### 簡単に言うと
業務Webアプリケーションでよく使う機能を、**再利用可能な部品**として提供するパッケージ集です。

### 具体例で理解する
インターンシップ課題で「残業管理システム」を作る場合：

**kitsなしの場合** 😓
- 通知機能をゼロから実装（2-3時間）
- レポート機能をゼロから実装（3-4時間）
- データインポート機能をゼロから実装（2時間）
- **合計: 7-9時間**

**kitsありの場合** 😊
- `kits.notifications`を使う（30分で設定）
- `kits.reports`を使う（30分で設定）
- `kits.io`を使う（30分で設定）
- **合計: 1.5時間**

**時短効果: 5.5-7.5時間！** 🚀

---

## 📚 kits機能一覧

| パッケージ | 状態 | 主な機能 | 使用課題例 | ドキュメント |
|-----------|------|---------|-----------|------------|
| **kits.notifications** | ✅ 完成 | メール通知、システム内通知、リマインダー | 残業申請、健診リマインダー | [詳細](./notifications/) |
| **kits.reports** | ✅ 完成 | グラフ生成、PDF出力、CSV/Excelエクスポート | 残業レポート、成長曲線 | [詳細](./reports/) |
| **kits.io** | ✅ 完成 | CSV/TSV/Excelインポート、重複チェック、文字コード検出 | 選手データ登録、蔵書登録 | [詳細](./io/) |
| kits.accounts | ✅ 完成 | ユーザー管理コマンド | 全課題 | - |
| kits.approvals | ✅ 完成 | 承認フロー（申請→承認→却下） | 残業申請、図書購入 | - |
| kits.audit | 🔶 部分完成 | 操作履歴記録 | 全課題 | - |
| kits.demos | ✅ 完成 | 参考実装（デモ申請システム） | 参考用 | - |

**凡例**
- ✅ 完成: そのまま使える
- 🚧 実装中: 現在作成中
- 📝 未実装: これから作る
- 🔶 部分完成: 基本機能は動く

---

## 🗂️ ドキュメント構造

各機能のドキュメントは以下の構造になっています：

```
kits/
├── notifications/                 # 通知機能
│   ├── 01_概要と目的.md          # なぜ必要？何ができる？（5分で読める）
│   ├── 02_設計思想.md            # どう設計した？なぜ？（10分）
│   ├── 03_実装の全体像.md        # ファイル構成と役割（10分）
│   ├── 04_コード解説.md          # 各コードの意味（30分）
│   ├── 05_使い方ガイド.md        # 実際の使用例（15分）
│   └── 06_よくある質問.md        # トラブルシューティング（必要時）
│
├── reports/                       # レポート機能（同様の構造）
│   ├── 00_実装ログ.md            # 実装作業の記録（リアルタイム更新）
│   ├── 01_概要と目的.md
│   ├── 02_設計思想.md
│   ├── 03_準備と環境構築.md      # Step1-2の詳細
│   ├── 04_データモデル.md        # Step3の詳細
│   └── ...
│
└── io/                            # データI/O機能（今後作成）
```

---

## 🎓 読み方ガイド

### 初めての方
1. 興味のある機能の`01_概要と目的.md`を読む（5分）
2. 実際に使いたい場合は`05_使い方ガイド.md`へ（15分）
3. エラーが出たら`06_よくある質問.md`を確認

### 実装を理解したい方
1. `01_概要と目的.md`でゴールを確認
2. `02_設計思想.md`で設計判断を理解
3. `03_実装の全体像.md`でファイル構成を把握
4. `04_コード解説.md`で詳細を学ぶ

### 同じような機能を作りたい方
1. `02_設計思想.md`で設計パターンを学ぶ
2. `03_実装の全体像.md`で構造を理解
3. `04_コード解説.md`でコードをコピー＆カスタマイズ

---

## 🔧 技術スタック

kitsパッケージで使用している主な技術：

| 技術 | 用途 | 使用パッケージ |
|-----|------|--------------|
| **Django 5.1.12** | Webフレームワーク | 全パッケージ |
| **Celery** | 非同期処理 | notifications |
| **Chart.js** | グラフ描画 | reports |
| **WeasyPrint** | PDF生成 | reports |
| **pandas** | データ処理 | reports, io |
| **openpyxl** | Excel読み書き | reports, io |

初心者の方でも、各ドキュメントで必要な技術を都度説明します。

---

## 💡 設計方針（全kits共通）

### 1. シンプルさ優先
複雑な構造を避け、ファイル数を最小限に保ちます。

**良い例** ✅
```
kits/notifications/
├── models.py       # モデル定義
├── services.py     # ビジネスロジック
├── tasks.py        # Celeryタスク
└── admin.py        # 管理画面
```

**悪い例** ❌
```
kits/notifications/
├── models/
│   ├── base.py
│   ├── notification.py
│   └── template.py
├── services/
│   ├── email.py
│   ├── sms.py
│   └── push.py
└── ... (ファイルが多すぎ)
```

### 2. 疎結合（他に依存しない）
kitsパッケージは、特定のアプリに依存しません。

**良い例** ✅
```python
# 汎用的な設計
def send_notification(user: User, template_code: str, context: dict):
    pass
```

**悪い例** ❌
```python
# 特定アプリに依存
from apps.overtime.models import OvertimeRequest
def send_overtime_notification(request: OvertimeRequest):
    pass
```

### 3. Django標準に従う
Djangoの慣習やベストプラクティスに従います。

---

## 🚀 クイックスタート

### kits.notificationsを使ってみる

```python
# 1. テンプレートを管理画面で作成（コードで自動作成も可）
# コード: "welcome_email"
# 件名: "ようこそ、{{user.get_full_name}}さん"
# 本文: "アカウント登録ありがとうございます..."

# 2. Pythonコードから通知送信
from kits.notifications.services import NotificationService

service = NotificationService()
notification = service.create_from_template(
    template_code="welcome_email",
    recipient=user,
    context={"user": user}
)

# 3. Celeryタスクで非同期送信
from kits.notifications.tasks import send_notification_task
send_notification_task.delay(notification.id)
```

詳しくは [notifications/05_使い方ガイド.md](./notifications/05_使い方ガイド.md) へ

---

## 📖 重要ドキュメント

### kitsパッケージの品質基準
- **[DOCUMENTATION_STANDARDS.md](./DOCUMENTATION_STANDARDS.md)** ⭐ - ドキュメント品質基準（v2.0）
  - 「初心者が超一流のエンジニアの実装をトレースして背景を理解できること」が目的
  - 設計判断の「なぜ」「代替案」「トレードオフ」の説明が最重要
  - 行数は参考値、内容の質が本質
- **[IMPLEMENTATION_CHECKLIST_TEMPLATE.md](./IMPLEMENTATION_CHECKLIST_TEMPLATE.md)** - 実装時のチェックリスト

### 品質チェックツール
- **`scripts/check_kits_docs_quality.py`** - ドキュメント品質の自動チェック
  ```bash
  # 使い方
  python3 scripts/check_kits_docs_quality.py io
  python3 scripts/check_kits_docs_quality.py --all
  ```

### 関連ドキュメント
- [KITS_CONTEXT.md](../KITS_CONTEXT.md) - kits全体の背景と戦略
- [インターンシップ戦略.md](/home/hirok/work/docs/インターンシップ戦略.md) - 100時間の時間配分
- [過去課題分析](../past-challenges/README.md) - kitsが役立つ場面

---

## ❓ よくある質問

### Q1: kitsパッケージは他のプロジェクトでも使える？
**A:** はい！ `pip install -e ~/work/school_diary` で任意のプロジェクトから利用できます。

### Q2: kitsを使わずに独自実装してもいい？
**A:** もちろんです。kitsは時短のための道具であり、強制ではありません。

### Q3: kitsのコードを改造してもいい？
**A:** はい！ただし、汎用性を保つために疎結合を維持してください。

### Q4: どのkitsから学べばいい？
**A:** `kits.notifications`が最も完成度が高く、参考になります。

---

**作成者**: Claude Code + hirok
**バージョン**: 1.0.0
**ライセンス**: MIT

#kits #school_diary #django #documentation #初心者向け
