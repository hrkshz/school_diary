# 課題2: 母子健康手帳デジタル化（2024年6月実施）

## 概要

架空の地方自治体より、母子健康手帳のデジタル化を進めるため、Webアプリのプロトタイプを開発する。

## 開発範囲

### 対象ページ
- **対象**: 「手帳の受け取り」から「3〜4か月児健康診査」まで（P.1-P.25）
- **除外**: 便色の確認の記録

### 主な記録項目
- 妊娠中の経過記録
- 出産の記録
- 新生児期の記録
- 乳児期の健康診査記録
- 予防接種の記録
- 成長曲線（身長・体重）

## 登場人物のロール

- **保護者**: 子どもの健康記録を管理・閲覧
- **役所（市区町村役場・保健所など）**: 手帳の交付、行政手続き
- **支援者（医師・歯科医師・助産師・保健師など）**: 健康診査の実施・記録

## 課題内容

### 課題1：デジタル化の実装（必須機能）

#### 1. 記録登録機能
- 測定結果を部員（子ども）ごとに登録できる
- 複数の子どもを管理できる（きょうだい対応）
- 日付・時刻とともに記録

#### 2. 保護者向け閲覧機能
- 部員（子ども）が自身の記録を時系列的に確認できる
- 成長曲線の可視化
- 予防接種スケジュールの確認

#### 3. 支援者向け閲覧機能
- 支援者が各利用者の記録を時系列的に確認できる
- 健康診査結果の入力
- 気になる点のフラグ付け

### 課題2：使いやすさの向上（任意）

- より現場で使いやすくなる機能追加
- ルール整備の提案
- **注**: 実装は任意（提案のみでも可）

## 開発要件

### 対応環境

#### デバイス
- Windows PC
- Mac
- iPhone
- iPad
- Android

#### ブラウザ
- Microsoft Edge
- Google Chrome
- Safari

#### 実行環境
- Ubuntu 22.04 LTS
- または Webホスティングサービス

### レスポンシブ対応
- モバイルファーストでのUI設計
- タッチ操作に最適化

## 提出物

### 1. ソースコード
- GitLab quest_1 Repository に格納
- デプロイ・動作手順書

### 2. ドキュメント（/doc以下）
- **利用マニュアル**（PDF または Markdown）
  - 保護者向け操作ガイド
  - 支援者向け操作ガイド
  - 役所向け管理ガイド

- **プレゼンテーション**
  - システム概要
  - 工夫点・アピール
  - 改善提案
  - 感想

## LabAppでの実装アプローチ

### 使用するkits

```python
# kits.accounts - ユーザー・ロール管理
# kits.audit - 変更履歴追跡
# kits.reports - 成長曲線・レポート生成
```

### モデル設計例

```python
class Child(models.Model):
    """子ども（部員）モデル"""
    family = models.ForeignKey('Family', related_name='children')
    name = models.CharField('氏名', max_length=100)
    birth_date = models.DateField('生年月日')
    gender = models.CharField('性別', max_length=10)

    history = HistoricalRecords()


class Family(models.Model):
    """家族（保護者）モデル"""
    guardian = models.ForeignKey(User, related_name='families')
    # 複数の子どもを管理


class HealthRecord(models.Model):
    """健康記録の基底モデル"""
    child = models.ForeignKey(Child, related_name='health_records')
    recorded_at = models.DateTimeField('記録日時')
    recorded_by = models.ForeignKey(User, related_name='recorded_health_records')
    record_type = models.CharField('記録種別', max_length=50)

    class Meta:
        abstract = True


class GrowthRecord(HealthRecord):
    """成長記録（身長・体重）"""
    height_cm = models.DecimalField('身長(cm)', max_digits=5, decimal_places=2)
    weight_kg = models.DecimalField('体重(kg)', max_digits=5, decimal_places=3)
    head_circumference_cm = models.DecimalField('頭囲(cm)', max_digits=5, decimal_places=2)


class HealthCheckup(HealthRecord):
    """健康診査記録"""
    checkup_type = models.CharField('健診種別', max_length=100)
    # 例: '新生児訪問指導', '1か月児健診', '3〜4か月児健診'
    doctor = models.ForeignKey(User, related_name='conducted_checkups')
    notes = models.TextField('所見')
    concerns = models.TextField('気になる点', blank=True)


class Vaccination(HealthRecord):
    """予防接種記録"""
    vaccine_name = models.CharField('ワクチン名', max_length=100)
    dose_number = models.IntegerField('接種回数')
    lot_number = models.CharField('ロット番号', max_length=50)
    clinic = models.CharField('接種場所', max_length=200)
    administrator = models.ForeignKey(User, related_name='administered_vaccinations')
```

## 開発のポイント

### 1. プライバシーとセキュリティ
- 個人情報保護法への準拠
- ロールベースのアクセス制御
- データの暗号化（保存時・通信時）

### 2. モバイル対応
- レスポンシブデザイン
- タッチ操作に最適化されたUI
- オフライン閲覧機能（PWA）

### 3. データ可視化
- 成長曲線のグラフ表示
- 標準値との比較
- 予防接種スケジュールのカレンダー表示

### 4. 使いやすさの工夫
- 音声入力対応
- よく使う記録のテンプレート
- リマインダー機能（健診・予防接種）

### 5. 紙の手帳との連携
- PDF出力機能（印刷用）
- QRコードでのデータ共有
- 既存の紙の手帳からのデータ移行

## 課題2の提案例

### 機能追加の提案
1. **成長予測機能**
   - AIを使った成長曲線の予測
   - 標準値からの乖離アラート

2. **地域連携機能**
   - 近隣の小児科・歯科の検索
   - 予防接種実施医療機関の表示

3. **情報提供機能**
   - 月齢・年齢に応じた育児情報
   - 地域の子育て支援イベント情報

4. **家族共有機能**
   - 祖父母など複数の保護者での情報共有
   - 保育園・幼稚園への情報提供

### ルール整備の提案
- デジタル手帳の法的位置づけの明確化
- 紙の手帳との併用期間の設定
- データ移行・引き継ぎルールの策定

## 参考情報

### 関連法令・ガイドライン
- 母子保健法
- 個人情報保護法
- 医療情報システムの安全管理に関するガイドライン

### 技術スタック例
- **グラフ描画**: Chart.js, Plotly
- **PDF生成**: WeasyPrint
- **PWA**: Workbox
- **認証**: django-allauth

### 参考事例
- デジタル母子手帳の先行事例調査
- 他自治体での導入事例
