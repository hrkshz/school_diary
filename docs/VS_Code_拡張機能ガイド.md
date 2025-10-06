# VS Code 拡張機能ガイド（初心者向け）

> 🔰 このガイドは、VS Codeを使い始めたばかりの方でも理解できるよう、図解や具体例を交えて説明します。

## 📋 目次

1. [インストール済み拡張機能一覧](#インストール済み拡張機能一覧)
2. [各拡張機能の使い方](#各拡張機能の使い方)
3. [ショートカット一覧](#ショートカット一覧)
4. [トラブルシューティング](#トラブルシューティング)

---

## 🎯 インストール済み拡張機能一覧

### 🐍 Python開発系

| 拡張機能 | 用途 | 自動/手動 |
|---------|------|----------|
| **Python** | Python基本機能 | 自動 |
| **Pylance** | 型チェック・補完 | 自動 |
| **Black Formatter** | コード整形 | 自動（保存時） |
| **Ruff** | コード品質チェック | 自動 |
| **autoDocstring** | ドキュメント生成 | 手動 |

### 🌐 Web開発系

| 拡張機能 | 用途 | 自動/手動 |
|---------|------|----------|
| **Django** | Djangoテンプレート | 自動 |
| **Prettier** | HTML/CSS/JS整形 | 自動（保存時） |

### 🧪 テスト・品質管理

| 拡張機能 | 用途 | 自動/手動 |
|---------|------|----------|
| **Test Explorer** | テスト実行・管理 | 手動 |
| **Coverage Gutters** | カバレッジ表示 | 手動 |

### 🛠️ 開発ツール

| 拡張機能 | 用途 | 自動/手動 |
|---------|------|----------|
| **GitLens** | Git履歴・作者表示 | 自動 |
| **Docker** | コンテナ管理 | 手動 |
| **PostgreSQL Client** | DB操作 | 手動 |
| **Rainbow CSV** | CSV表示強化 | 自動 |

---

## 📘 各拡張機能の使い方

### 1. **Black Formatter（コード自動整形）**

#### 🎯 何ができる？
- Pythonコードを自動で綺麗に整形
- PEP 8（Pythonの書き方ルール）に準拠

#### 🔧 使い方
**自動整形（保存時）：**
```python
# 保存前（汚いコード）
def calculate(x,y,z):return x+y*z

# Ctrl+S で保存すると...

# 保存後（綺麗なコード）
def calculate(x, y, z):
    return x + y * z
```

---

### 2. **autoDocstring（ドキュメント自動生成）**

#### 🎯 何ができる？
- 関数やクラスの説明文を自動生成
- Google形式のドキュメント作成

#### 🔧 使い方

1. 関数を書く
```python
def create_user(email, password, is_admin=False):
    # ← ここで「'''」と入力して Enter
```

2. 自動生成される
```python
def create_user(email, password, is_admin=False):
    """ユーザーを作成する。

    Args:
        email: メールアドレス
        password: パスワード
        is_admin: 管理者権限. Defaults to False.

    Returns:
        作成されたユーザーオブジェクト
    """
```

**ショートカット：** `Ctrl+Shift+2`（関数の下で押す）

---

### 3. **Coverage Gutters（テストカバレッジ表示）**

#### 🎯 何ができる？
- どのコードがテストされているか視覚化
- テストされていない箇所を赤で表示

#### 🔧 使い方

1. **テストを実行してカバレッジを生成**
```bash
docker-compose run --rm django coverage run -m pytest
docker-compose run --rm django coverage xml
```

2. **VS Codeで表示**
- 左下の「Watch」をクリック
- 緑の線 = テスト済み ✅
- 赤の線 = テスト未実施 ❌

**例：**
```python
def calculate_price(quantity, price):
    if quantity > 10:  # ← 緑（テスト済み）
        return quantity * price * 0.9
    else:  # ← 赤（テスト未実施）
        return quantity * price
```

---

### 4. **PostgreSQL Client（データベース操作）**

#### 🎯 何ができる？
- VS Code内でデータベース操作
- SQLの実行・テーブル確認

#### 🔧 使い方

1. **接続設定**
   - 左サイドバーの「Database」アイコンをクリック
   - 「+」ボタン → 「PostgreSQL」選択

2. **接続情報を入力**
```
Host: localhost
Port: 5432
Database: school_diary
User: debug
Password: debug
```

3. **SQLを実行**
```sql
-- 新規ファイル.sql を作成
SELECT * FROM users_user LIMIT 10;
-- Ctrl+Enter で実行
```

---

### 5. **GitLens（Git履歴の可視化）**

#### 🎯 何ができる？
- コードの作者・変更日時を表示
- ファイルの変更履歴を確認

#### 🔧 使い方

**行の作者を確認：**
- コードにカーソルを置くと、右端に作者と日時が表示
```python
def create_user():  # ← hirok, 2日前
    pass            # ← Claude, 1時間前
```

**ファイル履歴を見る：**
- ファイルを右クリック → 「View File History」

---

### 6. **Test Explorer（テスト実行）**

#### 🎯 何ができる？
- テストを個別に実行
- 失敗したテストだけ再実行

#### 🔧 使い方

1. **左サイドバーのフラスコアイコン**をクリック
2. テスト一覧が表示される
3. ▶️ ボタンで実行

**テストの状態：**
- ✅ 成功
- ❌ 失敗
- ⏭️ スキップ

---

### 7. **Docker（コンテナ管理）**

#### 🎯 何ができる？
- コンテナの起動・停止
- ログの確認

#### 🔧 使い方

1. **左サイドバーのDockerアイコン**をクリック
2. コンテナ一覧から操作

**よく使う操作：**
```bash
# 起動
右クリック → Start

# ログ確認
右クリック → View Logs

# 再起動
右クリック → Restart
```

---

## ⌨️ ショートカット一覧

### 🔥 最重要（毎日使う）

| 操作 | Windows/Linux | Mac |
|------|--------------|-----|
| **ファイル保存** | `Ctrl+S` | `Cmd+S` |
| **検索** | `Ctrl+F` | `Cmd+F` |
| **ファイルを開く** | `Ctrl+P` | `Cmd+P` |
| **コマンドパレット** | `Ctrl+Shift+P` | `Cmd+Shift+P` |
| **ターミナル開く** | `Ctrl+`` | `Cmd+`` |

### 🐍 Python専用

| 操作 | Windows/Linux | Mac |
|------|--------------|-----|
| **定義へジャンプ** | `F12` | `F12` |
| **参照を検索** | `Shift+F12` | `Shift+F12` |
| **リネーム** | `F2` | `F2` |
| **docstring生成** | `Ctrl+Shift+2` | `Cmd+Shift+2` |

### 🧪 テスト関連

| 操作 | Windows/Linux | Mac |
|------|--------------|-----|
| **テスト実行** | `Ctrl+Shift+T` | `Cmd+Shift+T` |
| **デバッグ実行** | `F5` | `F5` |

---

## 🔧 トラブルシューティング

### ❓ よくある質問

#### Q1: コードが自動整形されない
**A:** 設定を確認してください
1. `Ctrl+Shift+P` → 「Settings」と入力
2. 「Format On Save」にチェック

#### Q2: テストが見つからない
**A:** Test Explorerをリフレッシュ
1. テストアイコンをクリック
2. 上部の更新ボタンをクリック

#### Q3: Pylanceのエラーが多すぎる
**A:** pyrightconfig.jsonで調整済み
- 特に対応不要です

#### Q4: PostgreSQLに接続できない
**A:** Dockerコンテナを確認
```bash
docker-compose ps
# postgresqlコンテナがUpになっているか確認
```

#### Q5: カバレッジが表示されない
**A:** カバレッジファイルを生成
```bash
docker-compose run --rm django coverage run -m pytest
docker-compose run --rm django coverage xml
```

---

## 💡 便利な使い方のコツ

### 1. **マルチカーソル編集**
`Alt+クリック`で複数箇所を同時編集
```python
# user1, user2, user3 を同時に編集
user1 = create_user()  # ← Alt+クリック
user2 = create_user()  # ← Alt+クリック
user3 = create_user()  # ← Alt+クリック
# 全部同時に編集できる！
```

### 2. **ファイル名検索**
`Ctrl+P`でファイル名の一部を入力
```
Ctrl+P → "models" と入力
→ models.py がすぐ見つかる！
```

### 3. **全体検索**
`Ctrl+Shift+F`でプロジェクト全体を検索
```
例：「create_user」という関数がどこで使われているか調べる
```

---

## 🎓 初心者向け学習パス

### Week 1: 基本操作
- [ ] ファイルの開き方・保存を覚える
- [ ] Blackの自動整形に慣れる
- [ ] 基本的なショートカットを覚える

### Week 2: Python開発
- [ ] F12で定義ジャンプを使う
- [ ] autoDocstringでドキュメント作成
- [ ] Pylanceの補完機能を活用

### Week 3: テストとデバッグ
- [ ] Test Explorerでテスト実行
- [ ] Coverage Guttersでカバレッジ確認
- [ ] デバッガーの使い方を学ぶ

### Week 4: 応用
- [ ] GitLensで変更履歴を追跡
- [ ] PostgreSQL Clientでデータ確認
- [ ] Dockerコンテナの管理

---

## 📚 参考資料

- [VS Code公式ドキュメント（日本語）](https://code.visualstudio.com/docs)
- [Python in VS Code](https://code.visualstudio.com/docs/python/python-tutorial)
- [Django開発のベストプラクティス](https://docs.djangoproject.com/en/5.1/)

---

## 🆘 困ったときは

1. **エラーメッセージをコピー**してClaude/ChatGPTに聞く
2. **スクリーンショット**を撮って質問
3. **具体的な操作手順**を説明して相談

---

最終更新: 2025年1月
作成者: Claude with hirok