# テストデータ仕様書

> **対象環境**: 本番・ステージング
> **作成日**: 2025-10-25
> **データ生成コマンド**: `load_production_test_data`

---

## データ概要

- **学校種別**: 中学校
- **学年**: 1-3年（3学年）
- **クラス**: 各学年3クラス（A/B/C組）
- **生徒数**: 各クラス30名（合計270名）
- **連絡帳データ**: 過去14日分
- **パスワード**: 全アカウント統一（`password123`）

---

## アカウント一覧

### 必須アカウント（USER_TESTING_MANUAL.md準拠）

| ロール | メールアドレス | パスワード | 備考 |
|--------|---------------|-----------|------|
| システム管理者 | admin@example.com | password123 | 管理画面アクセス可 |
| 校長/教頭 | principal@example.com | password123 | 全校管理 |
| 1年生主任 | grade_leader@example.com | password123 | 1年全クラス閲覧可 |
| 1年A組担任 | teacher_1_a@example.com | password123 | Inbox Pattern全パターンあり |
| 1年A組1番 | student_1_a_01@example.com | password123 | P0分類（メンタル★1） |

### その他のアカウント

**学年主任** (3名):
- `grade_1_leader@example.com` / `password123` - 1年主任（上記と同一）
- `grade_2_leader@example.com` / `password123` - 2年主任
- `grade_3_leader@example.com` / `password123` - 3年主任

**担任** (9名):
- `teacher_{学年}_{クラス}@example.com` / `password123`
  - 例: `teacher_1_a@example.com`, `teacher_2_b@example.com`, `teacher_3_c@example.com`

**生徒** (270名):
- `student_{学年}_{クラス}_{番号}@example.com` / `password123`
  - 例: `student_1_a_01@example.com`, `student_2_b_15@example.com`, `student_3_c_30@example.com`
  - 番号は01-30（ゼロパディング）

---

## クラス構成

| 学年 | クラス | 担任 | 生徒数 | 備考 |
|------|--------|------|--------|------|
| 1年 | A組 | teacher_1_a@example.com | 30名 | Inbox Pattern全パターン |
| 1年 | B組 | teacher_1_b@example.com | 30名 | 通常データのみ |
| 1年 | C組 | teacher_1_c@example.com | 30名 | 通常データのみ |
| 2年 | A組 | teacher_2_a@example.com | 30名 | 通常データのみ |
| 2年 | B組 | teacher_2_b@example.com | 30名 | 通常データのみ |
| 2年 | C組 | teacher_2_c@example.com | 30名 | 通常データのみ |
| 3年 | A組 | teacher_3_a@example.com | 30名 | 通常データのみ |
| 3年 | B組 | teacher_3_b@example.com | 30名 | 通常データのみ |
| 3年 | C組 | teacher_3_c@example.com | 30名 | 通常データのみ |

---

## Inbox Patternテストデータ（1年A組のみ）

**担任ダッシュボード（teacher_1_a@example.com）でテスト可能な全パターン**

| 分類 | 優先度 | 生徒数 | アカウント例 | 条件 |
|------|--------|--------|--------------|------|
| P0: 重要 | 最高 | 2名 | student_1_a_01, student_1_a_02 | メンタル★1（昨日提出） |
| P1: 要注意 | 高 | 2名 | student_1_a_03, student_1_a_04 | 3日連続低下（5→4→3） |
| P1.5: 要対応タスク | 高 | 3名 | student_1_a_05-07 | internal_action設定済み |
| P2-1: 未提出 | 中 | 5名 | student_1_a_08-12 | 昨日のエントリーなし |
| P2-2: 未読 | 中 | 5名 | student_1_a_13-17 | 昨日提出、未読 |
| P2-3: 反応待ち | 中 | 5名 | student_1_a_18-22 | 昨日提出、既読、反応未選択 |
| P3: 完了 | 低 | 8名 | student_1_a_23-30 | 昨日提出、既読、反応済み |

### 詳細データ仕様

**P0: 重要（メンタル★1）**
- 対象: student_1_a_01, student_1_a_02
- 昨日のエントリー: mental_condition=1, health_condition=3, is_read=False
- 過去13日: 通常データ（mental=3-5, 既読、反応済み）

**P1: 要注意（3日連続低下）**
- 対象: student_1_a_03, student_1_a_04
- 3日前: mental_condition=5
- 2日前: mental_condition=4
- 昨日: mental_condition=3, is_read=False
- 過去11日: 通常データ（mental=4-5）

**P1.5: 要対応タスク**
- 対象: student_1_a_05, student_1_a_06, student_1_a_07
- 昨日のエントリー: internal_action=NEEDS_FOLLOW_UP, action_status=PENDING, is_read=True
- 過去13日: 通常データ

**P2-1: 未提出**
- 対象: student_1_a_08-12
- 昨日のエントリー: なし（データなし）
- 2日前以前: 通常データあり

**P2-2: 未読**
- 対象: student_1_a_13-17
- 昨日のエントリー: mental_condition=4, health_condition=4, is_read=False
- 過去13日: 通常データ

**P2-3: 反応待ち**
- 対象: student_1_a_18-22
- 昨日のエントリー: is_read=True, public_reaction=None（反応未選択）
- 過去13日: 通常データ

**P3: 完了**
- 対象: student_1_a_23-30
- 昨日のエントリー: is_read=True, public_reaction=THUMBS_UP
- 過去13日: 通常データ

---

## 共有メモ（TeacherNote）

**1年A組のみ2件作成**

| 対象生徒 | 作成者 | 内容 | 既読者 |
|---------|--------|------|--------|
| student_1_a_01 | teacher_1_a@example.com | 最近、部活で悩んでいるようです。学年で共有します。 | grade_leader@example.com |
| student_1_a_02 | teacher_1_a@example.com | 保護者面談希望あり。学年主任に報告済み。 | grade_leader@example.com |

---

## 実行方法

### 開発環境（Docker）

```bash
# コンテナ内で実行
docker compose -f docker-compose.local.yml run --rm django python manage.py load_production_test_data --clear
```

### 本番環境（EC2）

```bash
# ホストからコンテナにファイル転送
scp -i ~/.ssh/school-diary-key.pem \
  school_diary/diary/management/commands/load_production_test_data.py \
  ubuntu@43.206.211.105:/tmp/

# SSH接続
ssh -i ~/.ssh/school-diary-key.pem ubuntu@43.206.211.105

# コンテナIDを確認
docker ps | grep django

# ファイルをコンテナにコピー
docker cp /tmp/load_production_test_data.py <CONTAINER_ID>:/app/school_diary/diary/management/commands/

# コマンド実行
docker exec <CONTAINER_ID> python manage.py load_production_test_data --clear
```

### オプション

- `--clear`: 既存の@example.comアカウント・関連データを削除してから作成（推奨）
- オプションなし: 既存データに追加（重複エラーの可能性あり）

---

## データ再現性

- `--clear`オプション使用時、毎回同一のデータが作成される
- ランダム要素: 生徒の姓名のみ（ランダム抽出）
- Inbox Patternの分類は固定（student_1_a_01-30の番号で決定）

---

## 注意事項

### データ削除範囲（--clear実行時）

以下のデータが削除される：

- `User.objects.filter(email__endswith="@example.com")` - テストアカウントのみ
- `DiaryEntry.objects.all()` - 全連絡帳データ
- `ClassRoom.objects.all()` - 全クラスデータ
- `TeacherNote.objects.all()` - 全共有メモ
- `TeacherNoteReadStatus.objects.all()` - 全既読管理データ

本番環境の実データと混在させないこと。

### 実行時間

- 開発環境: 約5-10秒
- 本番環境: 約10-20秒

### 作成データ量

- ユーザー: 577名（管理者5 + 学年主任3 + 担任9 + 生徒270 + その他）
- クラス: 9クラス
- 連絡帳: 3775件（270名 × 14日 - 未提出分）
- 共有メモ: 2件

---

## テストシナリオ例

### 担任ダッシュボード確認

1. `teacher_1_a@example.com`でログイン
2. Inbox Patternの6カテゴリ（P0-P3）が全て表示されることを確認
3. 各カテゴリの生徒数が仕様通りか確認

### 学年主任ダッシュボード確認

1. `grade_leader@example.com`でログイン
2. 1年全クラス（A/B/C組）の生徒一覧が閲覧可能か確認
3. 共有メモの既読管理が動作するか確認

### 生徒機能確認

1. `student_1_a_01@example.com`でログイン（P0分類）
2. 過去の連絡帳が閲覧可能か確認
3. 新規連絡帳が作成可能か確認

---

**作成日**: 2025-10-25
**管理コマンド**: `school_diary/diary/management/commands/load_production_test_data.py`
