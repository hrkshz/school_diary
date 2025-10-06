# 課題3: 野球部タレントマネジメントシステム（2025年10月採用）

## 概要

神奈川県立JPT高校野球部（架空）が、部員一人一人のスキルとチーム実力を可視化するため、タレントマネジメントシステムのPoCを開発する。

## 現在の運用

### 記録測定日の実施
- **頻度**: 2か月に1度、全部員参加
- **記録方法**: 紙で配布
- **課題**: 時系列整理や傾向分析が未実施

### 測定項目

#### 走力
- 50m走（秒）
- ベースランニング（秒）

#### 肩力
- 遠投（m）
- ストレート球速（km/h）

#### 打力
- 打球速度（km/h）
- スイング速度（km/h）

#### 筋力
- ベンチプレス（kg）
- スクワット（kg）

## 登場人物のロール

- **部員（野球部の学生）**: 自分の測定記録を確認
- **マネージャー（学生）**: 測定結果の記入・承認フロー発行
- **コーチ（部員の指導者）**: 最終承認・全部員の記録閲覧・部員管理
- **監督（最終責任者）**: 全部員の記録閲覧・部員管理（承認には関与しない）

## 課題1：必須機能

### 測定結果の承認フロー

```
1. マネージャー → 測定結果を記入し承認フロー発行
         ↓
2. 部員 → 自分の記録を確認し承認
         ↓
3. コーチ → 最終確認し確定
```

**重要**: 監督は承認フローに関与しない

### 各ロールの機能要件

#### マネージャー
- 測定記録結果の入力
- 承認フローの発行
- 測定日の設定・管理

#### 部員
- 測定記録結果の承認（自分の記録のみ）
- 自身の測定記録の時系列閲覧
- 過去データとの比較

#### コーチ
- 測定記録の最終承認
- 全部員の測定記録の閲覧
- 部員の作成（新入部）
- 部員の退部処理

#### 監督
- 全部員の測定記録の閲覧
- 部員の作成（新入部）
- 部員の退部処理
- 部員の引退処理

## 課題2：プラスアルファの提案

### 可視化機能
- 監督・コーチがチーム全体の傾向を可視化・確認できる機能
- 項目別の平均値推移
- 部員間の比較
- ポジション別の分析

### 改善提案
- より使いやすくなる機能追加
- 効果が出るルール整備の提案
- **注**: 実装は任意（提案のみでも可）

## ヒント

### 参考資料
- 過去2回分の記録.xlsx（活用は任意）
- 実データに基づく分析が可能

### アプローチ
- ヒアリング結果の活用
- または独自の仮説立て

## 提出物

### 1. ソースコード
- GitLab quest_1 Repository mainブランチ
- デプロイ・動作手順

### 2. ドキュメント（/doc以下）
- **利用マニュアル**（必須）
  - 各ロールごとの操作方法
  - 画面遷移図

- **ER図**（必須）
  - データベース設計図
  - モデル間の関係性

- **テストアカウント一覧**（必須）
  - 各ロールのテストユーザー
  - ログイン情報

- **工夫点・アピール**
  - 実装した機能の特徴
  - 技術的なチャレンジ

- **改善提案のプレゼンテーション**
  - 課題2の提案内容
  - 期待される効果

- **感想**
  - 開発を通じて学んだこと

## LabAppでの実装アプローチ

### 使用するkits

```python
# kits.accounts - ユーザー・ロール管理
# kits.approvals - 承認フロー（FSM）
# kits.audit - 変更履歴追跡
# kits.reports - データ可視化・レポート生成
```

### モデル設計例

```python
class Player(models.Model):
    """部員モデル"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_number = models.CharField('学籍番号', max_length=20, unique=True)
    grade = models.IntegerField('学年')  # 1, 2, 3
    position = models.CharField('守備位置', max_length=50)
    # 例: '投手', '捕手', '内野手', '外野手'

    is_active = models.BooleanField('在籍中', default=True)
    joined_at = models.DateField('入部日')
    retired_at = models.DateField('引退日', null=True, blank=True)

    history = HistoricalRecords()


class MeasurementSession(models.Model):
    """測定日（セッション）モデル"""
    date = models.DateField('測定日')
    season = models.CharField('シーズン', max_length=20)  # 例: '2024年10月'
    notes = models.TextField('備考', blank=True)

    created_by = models.ForeignKey(User, related_name='created_sessions')
    created_at = models.DateTimeField(auto_now_add=True)


class MeasurementRecord(models.Model):
    """測定記録モデル（承認フロー付き）"""
    session = models.ForeignKey(MeasurementSession, related_name='records')
    player = models.ForeignKey(Player, related_name='measurement_records')

    # 測定項目
    sprint_50m = models.DecimalField('50m走(秒)', max_digits=5, decimal_places=2, null=True)
    base_running = models.DecimalField('ベースランニング(秒)', max_digits=5, decimal_places=2, null=True)
    long_throw = models.DecimalField('遠投(m)', max_digits=5, decimal_places=2, null=True)
    pitch_speed = models.DecimalField('球速(km/h)', max_digits=5, decimal_places=2, null=True)
    bat_speed = models.DecimalField('打球速度(km/h)', max_digits=5, decimal_places=2, null=True)
    swing_speed = models.DecimalField('スイング速度(km/h)', max_digits=5, decimal_places=2, null=True)
    bench_press = models.DecimalField('ベンチプレス(kg)', max_digits=5, decimal_places=2, null=True)
    squat = models.DecimalField('スクワット(kg)', max_digits=5, decimal_places=2, null=True)

    # 承認フロー（django-fsm）
    status = FSMField(default='draft', max_length=50)
    # draft → submitted → player_approved → coach_confirmed

    # 承認者記録
    manager = models.ForeignKey(User, related_name='managed_records', null=True)
    player_approved_at = models.DateTimeField('部員承認日時', null=True)
    coach = models.ForeignKey(User, related_name='confirmed_records', null=True)
    coach_confirmed_at = models.DateTimeField('コーチ確認日時', null=True)

    history = HistoricalRecords()

    class Meta:
        unique_together = ['session', 'player']


class TeamStatistics(models.Model):
    """チーム統計モデル"""
    session = models.OneToOneField(MeasurementSession, related_name='statistics')

    # 各項目の平均値
    avg_sprint_50m = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    avg_base_running = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    avg_long_throw = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    avg_pitch_speed = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    avg_bat_speed = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    avg_swing_speed = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    avg_bench_press = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    avg_squat = models.DecimalField(max_digits=5, decimal_places=2, null=True)

    calculated_at = models.DateTimeField(auto_now=True)
```

### 状態遷移図

```
draft            # マネージャーが入力中
  ↓
submitted        # 部員承認待ち
  ↓
player_approved  # コーチ確認待ち
  ↓
coach_confirmed  # 確定
```

## 開発のポイント

### 1. 承認フロー
- マネージャー → 部員 → コーチの3段階
- 監督は閲覧のみ（承認には関与しない）
- 各段階で差し戻し機能

### 2. データ可視化
- 個人の成長曲線（レーダーチャート）
- チーム全体の傾向分析（折れ線グラフ）
- ポジション別の比較
- 前回比較・目標設定

### 3. ロール管理
```python
# グループ定義
- manager_group: マネージャー
- player_group: 部員
- coach_group: コーチ
- director_group: 監督
```

### 4. 使いやすさの工夫
- 一括入力機能（Excel取り込み）
- モバイル対応（測定現場での入力）
- 印刷機能（紙の記録表との併用）

## 課題2の提案例

### 可視化機能
1. **チームダッシュボード**
   - 全体の平均値推移
   - 項目別の分布図
   - 学年別・ポジション別の比較

2. **個人分析レポート**
   - 強み・弱みの自動判定
   - 改善ポイントの提示
   - 目標設定支援

3. **競合比較機能**
   - 全国平均との比較
   - 強豪校との比較データ

### 改善提案
1. **トレーニング連携**
   - 弱点補強のトレーニングメニュー提示
   - 個別トレーニング計画の作成

2. **モチベーション向上**
   - 成長の可視化（ビフォーアフター）
   - ランキング表示（項目別）
   - 目標達成バッジ

3. **保護者連携**
   - 保護者向けレポート生成
   - 成長記録の共有

4. **データ分析**
   - 怪我予測（筋力バランス）
   - パフォーマンス予測
   - 適正ポジション提案

## 参考情報

### データ可視化ライブラリ
- **Python**: matplotlib, seaborn, plotly
- **JavaScript**: Chart.js, D3.js, Plotly.js

### Excel連携
- `openpyxl`: Excel読み書き
- `pandas`: データ分析
- `django-import-export`: CSV/Excelインポート

### 統計分析
- 平均値・中央値・標準偏差
- 相関分析（項目間の関係性）
- 回帰分析（成長予測）

### テストデータ
- 過去2回分の記録.xlsxを活用
- 実データに基づくダッシュボード作成
- 統計的な分析結果の提示
