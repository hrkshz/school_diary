# 課題4: 図書館システム（2025年6月実施）

## 概要

架空の地方自治体で、5つの公立高校の図書館システムを統合し、学校間での貸し出し（図書館間貸出）を実装する。GIGAスクール構想の導入により全生徒にWindows PCとメールアドレスが配布されたことを受け、従来各学校でバラバラに運用されていた図書館システムを統一する。

## 登場人物のロール

- **生徒**: 資料の検索・予約・貸出・返却
- **管理者**: 生徒アカウントの登録・削除
- **司書**: 資料の追加・廃棄・図書館間貸出の運用

## 現在の各図書館の運用

### A高校・B高校の運用
- **認証方式**: 図書館カード（一次元バーコード）
- **貸出**: カードと資料のバーコードをスキャン
- **返却**: 資料のバーコードをスキャン、返却用棚へ
- **特徴**: シンプルなバーコードベースの運用

### C高校・D高校の運用
- **認証方式**: 図書館アカウント（メールアドレスベース）
- **貸出**: アカウントでログイン後、資料のバーコードをスキャン
- **返却**: 資料のバーコードをスキャン、返却用棚へ
- **特徴**: 予約機能、メール通知機能あり
- **通知**: 予約資料の準備完了時に自動メール送信
- **予約**: 一定期間貸し出しがない場合、自動キャンセル

### E高校の運用
- **認証方式**: NFCカード（バーコードとNFC両対応）
- **貸出**: カードと資料のNFCタグを読み込み
- **返却**: 資料のNFCタグをスキャン、返却用棚へ
- **特徴**: NFC対応、予約機能、メール通知機能あり
- **通知**: C・D高校と同様

## 課題内容

### 課題1：図書館システムのプロトタイプ開発（必須）

#### 【生徒の機能】
- 既存の資料の検索
- 既存資料への貸し出し予約
- 貸出中の資料への順番待ち
- 資料の貸出・返却
- パスワード変更

#### 【システムの機能】
- 予約資料の準備の通知
- 返却予定日の自動リマインド
- 他校へ送付する資料のリスト化

#### 【管理者機能】
- 新入生徒のアカウント登録
- 卒業・退学生徒のアカウント削除

#### 【司書の機能】
- 資料の追加
- 資料の廃棄

### 課題2：業務改善提案

- 現場で使いやすくなるルール整備
- 業務改善の提案
- **注**: 実装は任意（提案のみでも可）

## 図書館間貸出の仕様

### 図書館間貸出の流れ

```
1. 生徒が他校の資料を予約
         ↓
2. 毎週金曜15時で締め切り（祝祭日の場合は最後の開校日）
         ↓
3. 資料が貸出中の場合、返却を待つ
         ↓
4. 司書・図書委員が運送箱にまとめる
         ↓
5. 金曜17時に業者が回収
         ↓
6. 業者がシステム出力を元に各学校に振り分け
         ↓
7. 翌開校日の朝10時に届く
         ↓
8. 司書・図書委員がシステムに登録・専用棚へ移動
         ↓
9. システムが予約者に通知
```

## 技術的な考慮事項

### 最終的なゴール
- 5つの図書館の資料を横断検索し、必要な資料を取り寄せられる
- 図書館の運用ルールを統一し、職員の教育・運用コストを下げる
- 最終的には「地理的に分散した1つの図書館」として運用

### データ移行の課題
- **問題**: 各図書館のバーコードIDの採番ルールが異なり、重複する可能性がある
- **解決案**: 新しい採番ルールを策定し、重複した資料には新規に採番
- **既存データ**: 各図書館システムからUTF-8のTSV形式でエクスポート可能

### 環境要件
- **対応環境**: Windows PC（GIGAスクール構想）
- **アクセス方式**: Webシステム（全機能をPC・生徒PCで利用可能）
- **PoC環境**: インターネット経由でアクセス
- **本番環境**: 地方自治体のイントラネットまたはガバメントクラウド

### 各図書館の仕様
- **蔵書数**: 各図書館約15,000冊
- **蔵書内容**:
  - 一般書籍（学習参考資料・小説・辞書等）
  - 各学科の特色を反映した専門書
    - 大学進学特化校: 赤本全巻
    - 情報技術科: オライリー書籍全巻
    - メディア情報科: マンガ・ライトノベル
- **書架**: すべて開架（閉架なし）

## 提出物

### 1. Webアプリケーション本体
- ソースコード（GitLab mainブランチ）
- デプロイ・動作手順

### 2. ドキュメント（/doc以下に配置）
- **利用マニュアル**（PDF または Markdown）
  - 生徒向け操作方法
  - 司書向け操作方法
  - 管理者向け操作方法

- **ER図**
  - データベース設計図
  - モデル間の関係性

- **工夫点・アピール**
  - 実装した機能の工夫
  - 技術的なチャレンジ

- **業務改善提案**
  - 現場で使いやすくなる提案
  - 運用ルールの整備案

- **感想**
  - 開発を通じて学んだこと
  - 苦労した点と解決方法

## LabAppでの実装アプローチ

### 使用するkits

```python
# kits.accounts - ユーザー・ロール管理（生徒・管理者・司書）
# kits.audit - 変更履歴追跡
# kits.notifications - メール通知（予約準備・返却リマインド）
# kits.io - TSVインポート（既存データ移行）
# kits.reports - 送付資料リスト生成
```

### モデル設計例

```python
class School(models.Model):
    """学校モデル"""
    name = models.CharField('学校名', max_length=100)
    code = models.CharField('学校コード', max_length=10, unique=True)
    # 例: 'A', 'B', 'C', 'D', 'E'
    address = models.TextField('住所')

    history = HistoricalRecords()


class Student(models.Model):
    """生徒モデル"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, related_name='students')
    student_number = models.CharField('学籍番号', max_length=20, unique=True)
    grade = models.IntegerField('学年')  # 1, 2, 3
    email = models.EmailField('メールアドレス', unique=True)

    is_active = models.BooleanField('在籍中', default=True)
    enrolled_at = models.DateField('入学日')
    graduated_at = models.DateField('卒業日', null=True, blank=True)

    history = HistoricalRecords()


class Book(models.Model):
    """資料モデル"""
    # 基本情報
    isbn = models.CharField('ISBN', max_length=13, blank=True)
    title = models.CharField('タイトル', max_length=500)
    author = models.CharField('著者', max_length=200)
    publisher = models.CharField('出版社', max_length=200)
    published_date = models.DateField('出版日', null=True, blank=True)
    category = models.CharField('分類', max_length=100)

    # 管理情報
    school = models.ForeignKey(School, related_name='books')
    barcode_id = models.CharField('バーコードID', max_length=50, unique=True)
    # 新しい採番ルール: {学校コード}-{連番8桁} 例: A-00001234

    acquisition_date = models.DateField('受入日')
    status = models.CharField('状態', max_length=20, default='available')
    # available: 利用可能, borrowed: 貸出中, reserved: 予約中,
    # in_transit: 配送中, discarded: 廃棄済み

    history = HistoricalRecords()


class Reservation(models.Model):
    """予約モデル"""
    book = models.ForeignKey(Book, related_name='reservations')
    student = models.ForeignKey(Student, related_name='reservations')

    # 予約情報
    reserved_at = models.DateTimeField('予約日時', auto_now_add=True)
    pickup_school = models.ForeignKey(
        School,
        related_name='pickup_reservations',
        help_text='受取学校'
    )

    # 状態管理
    status = models.CharField('予約状態', max_length=20, default='pending')
    # pending: 予約待ち, preparing: 準備中, ready: 受取可能,
    # picked_up: 受取済み, cancelled: キャンセル, expired: 期限切れ

    # 図書館間貸出情報
    is_inter_library = models.BooleanField('図書館間貸出', default=False)
    shipment_date = models.DateField('発送日', null=True, blank=True)
    arrival_date = models.DateField('到着日', null=True, blank=True)

    # 通知
    notified_at = models.DateTimeField('通知日時', null=True, blank=True)

    # 順番待ち
    queue_position = models.IntegerField('順番', default=1)

    history = HistoricalRecords()

    class Meta:
        ordering = ['reserved_at']


class Loan(models.Model):
    """貸出モデル"""
    book = models.ForeignKey(Book, related_name='loans')
    student = models.ForeignKey(Student, related_name='loans')
    reservation = models.ForeignKey(
        Reservation,
        related_name='loan',
        null=True,
        blank=True
    )

    # 貸出情報
    borrowed_at = models.DateTimeField('貸出日時', auto_now_add=True)
    due_date = models.DateField('返却期限日')
    returned_at = models.DateTimeField('返却日時', null=True, blank=True)

    # 図書館情報
    borrowing_school = models.ForeignKey(
        School,
        related_name='borrowing_loans',
        help_text='貸出学校'
    )
    returning_school = models.ForeignKey(
        School,
        related_name='returning_loans',
        null=True,
        blank=True,
        help_text='返却学校'
    )

    # 延滞管理
    is_overdue = models.BooleanField('延滞中', default=False)
    reminder_sent_at = models.DateTimeField('リマインド送信日時', null=True, blank=True)

    history = HistoricalRecords()


class InterLibraryShipment(models.Model):
    """図書館間配送モデル"""
    # 配送情報
    from_school = models.ForeignKey(
        School,
        related_name='outgoing_shipments',
        help_text='発送元学校'
    )
    to_school = models.ForeignKey(
        School,
        related_name='incoming_shipments',
        help_text='発送先学校'
    )

    # 日程
    cutoff_date = models.DateTimeField('締切日時')
    # 毎週金曜15時（祝祭日の場合は最後の開校日）
    pickup_date = models.DateTimeField('回収日時')
    # 毎週金曜17時
    delivery_date = models.DateTimeField('配達日時')
    # 翌開校日の朝10時

    # 状態
    status = models.CharField('配送状態', max_length=20, default='preparing')
    # preparing: 準備中, picked_up: 回収済み, in_transit: 配送中,
    # delivered: 配達済み, registered: 登録完了

    # 関連予約
    reservations = models.ManyToManyField(Reservation, related_name='shipments')

    history = HistoricalRecords()

    class Meta:
        ordering = ['-cutoff_date']


class Librarian(models.Model):
    """司書モデル"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, related_name='librarians')
    employee_number = models.CharField('職員番号', max_length=20, unique=True)

    history = HistoricalRecords()
```

### 状態遷移図

#### 予約の状態遷移
```
pending       # 予約待ち
  ↓
preparing     # 準備中（図書館間貸出の場合は配送中）
  ↓
ready         # 受取可能（通知送信済み）
  ↓
picked_up     # 受取済み（貸出に移行）

# 例外パス
pending/preparing → cancelled  # キャンセル
ready → expired                # 期限切れ
```

#### 貸出の状態遷移
```
borrowed      # 貸出中
  ↓
(期限経過)
  ↓
overdue       # 延滞中（is_overdue=True）
  ↓
returned      # 返却済み
```

#### 図書館間配送の状態遷移
```
preparing     # 準備中（金曜15時まで）
  ↓
picked_up     # 回収済み（金曜17時）
  ↓
in_transit    # 配送中
  ↓
delivered     # 配達済み（翌開校日10時）
  ↓
registered    # 登録完了（司書が専用棚に移動・システム登録）
```

## 開発のポイント

### 1. 横断検索機能
- 5つの学校の資料を一括検索
- タイトル・著者・ISBN・分類での検索
- 学校別フィルタリング
- 在庫状況の表示（利用可能・貸出中・予約中等）

```python
# 検索例
books = Book.objects.filter(
    Q(title__icontains=query) |
    Q(author__icontains=query) |
    Q(isbn__icontains=query),
    status__in=['available', 'borrowed']
).select_related('school').order_by('school', 'title')
```

### 2. 予約・順番待ち機能
- 貸出中の資料への予約
- 複数予約時の順番管理（queue_position）
- 予約キャンセル時の順番繰り上げ
- 予約期限（一定期間貸出がない場合は自動キャンセル）

```python
# 順番待ちの実装例
def add_to_queue(book, student):
    """予約キューに追加"""
    max_position = Reservation.objects.filter(
        book=book,
        status__in=['pending', 'preparing', 'ready']
    ).aggregate(Max('queue_position'))['queue_position__max'] or 0

    reservation = Reservation.objects.create(
        book=book,
        student=student,
        queue_position=max_position + 1,
        is_inter_library=(book.school != student.school)
    )
    return reservation
```

### 3. 図書館間貸出の自動化
- 毎週金曜15時の締切チェック（Celery定期タスク）
- 配送リストの生成（PDF/CSV）
- 配送状態の追跡
- 到着通知の自動送信

```python
# Celeryタスク例
@shared_task
def process_weekly_shipments():
    """毎週金曜15時に実行"""
    today = timezone.now()

    # 金曜15時の締切
    if today.weekday() != 4 or today.hour != 15:
        return

    # 図書館間予約を集計
    pending_reservations = Reservation.objects.filter(
        status='pending',
        is_inter_library=True
    )

    # 学校ペアごとにShipmentを作成
    # ...
```

### 4. 通知機能
- **予約準備完了通知**: 資料が受取可能になったらメール送信
- **返却リマインド**: 返却期限の3日前にメール送信
- **延滞通知**: 返却期限を過ぎた場合にメール送信
- **配送通知**: 図書館間貸出の到着時にメール送信

```python
# 通知例
from kits.notifications.email import send_notification

def notify_reservation_ready(reservation):
    """予約準備完了通知"""
    send_notification(
        to=reservation.student.email,
        subject='予約資料の準備が完了しました',
        template='library/email/reservation_ready.html',
        context={'reservation': reservation}
    )
    reservation.notified_at = timezone.now()
    reservation.save()
```

### 5. データ移行（TSVインポート）
- 既存5システムからのTSVインポート
- バーコードIDの重複チェック
- 重複時の新規採番
- インポートログの記録

```python
# TSVインポート例（kits.io活用）
from kits.io.importers import TSVImporter

class BookImporter(TSVImporter):
    """資料インポート"""

    def process_row(self, row, school_code):
        # バーコードIDの重複チェック
        old_barcode = row['barcode_id']
        if Book.objects.filter(barcode_id=old_barcode).exists():
            # 新規採番: {学校コード}-{連番8桁}
            new_barcode = self.generate_new_barcode(school_code)
        else:
            new_barcode = old_barcode

        Book.objects.create(
            school=School.objects.get(code=school_code),
            barcode_id=new_barcode,
            title=row['title'],
            author=row['author'],
            # ...
        )
```

### 6. ロール管理
```python
# グループ定義
- student_group: 生徒（資料の検索・予約・貸出・返却）
- librarian_group: 司書（資料の追加・廃棄・配送管理）
- admin_group: 管理者（生徒アカウントの登録・削除）
```

### 7. セキュリティ
- パスワード変更機能
- ロールベースのアクセス制御
- 生徒は自分の予約・貸出のみ閲覧可能
- 司書は自校の資料のみ管理可能
- 管理者は自校の生徒のみ管理可能

## 課題2の提案例

### 機能追加の提案

1. **モバイルアプリ対応**
   - PWAでのオフライン検索
   - プッシュ通知

2. **AI推薦機能**
   - 貸出履歴からの推薦
   - 学科別の人気資料

3. **読書記録・レビュー**
   - 読了記録
   - 書評・レーティング
   - 読書ランキング

4. **統計・可視化**
   - 学校別貸出統計
   - 人気資料ランキング
   - 学科別利用傾向

### ルール整備の提案

1. **図書館間貸出の最適化**
   - 配送頻度の見直し（週2回等）
   - 緊急配送オプション
   - 配送コストの可視化

2. **予約期限の明確化**
   - 準備完了後の受取期限（例: 1週間）
   - 期限切れ後の自動キャンセル

3. **延滞ペナルティ**
   - 延滞回数に応じた貸出制限
   - 段階的な通知

4. **データ標準化**
   - 新規資料の登録ルール
   - メタデータの品質管理
   - 重複資料の統合

5. **運用の段階的移行**
   - Phase 1: 校内システムの統一
   - Phase 2: 図書館間貸出の試験運用
   - Phase 3: 地理的に分散した1つの図書館の実現

## 参考情報

### 関連するDjangoパッケージ
- `django-simple-history`: 履歴管理
- `django-anymail`: メール通知
- `celery`: 定期タスク（週次配送処理）
- `django-import-export`: TSVインポート
- `django-filter`: 横断検索

### セキュリティ考慮事項
- ロールベースのアクセス制御
- 個人情報保護（貸出履歴等）
- 監査ログの記録

### 参考事例
- 大学図書館のOPAC（蔵書検索システム）
- 公共図書館の相互貸借システム
- 国立国会図書館のデジタルアーカイブ

### 技術スタック例
- **検索**: django-filter, PostgreSQL全文検索
- **通知**: django-anymail, Celery Beat
- **データ移行**: pandas, django-import-export
- **認証**: django-allauth
