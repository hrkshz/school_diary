# 課題1: 残業管理システム（2024年11月実施）

## 概要

昭和から続く架空の会社で、残業管理を15分単位から1分単位に変更するため、残業管理システムのプロトタイプを開発する。

## 登場人物のロール

- **社員**: 残業申請を行う
- **取りまとめ役（次長）**: 申請を取りまとめる
- **承認者（課長）**: 最終承認を行う

## 課題内容

### 課題1：必須機能の実装

1. **ロール別管理画面**
   - 社員用管理画面
   - 次長用管理画面
   - 課長用管理画面

2. **申請・承認フロー**
   - 社員が残業を申請
   - 次長が取りまとめ
   - 課長が最終承認

3. **申請書の印刷機能**
   - 承認済み申請書のPDF出力

4. **月次処理**
   - 人事部門への提出機能
   - 月次集計機能

### 課題2：業務改善提案

- 現場で使いやすくなるようなルール整備や業務改善の提案
- **重要**: 長年続く企業のため、現場の反感を買わないよう配慮が必要

## 技術的な考慮事項

### 時間管理の変更点
- **従来**: 15分単位での残業管理
- **新方式**: 1分単位での残業管理
- **影響**: 既存の運用フローとの整合性を保ちつつ変更する必要がある

### 承認フロー
```
社員 → 次長（取りまとめ） → 課長（最終承認） → 確定
```

## 提出物

### 1. Webアプリケーション本体
- ソースコード（GitLab mainブランチ）
- デプロイ・動作手順

### 2. ドキュメント（/doc以下に配置）
- **利用マニュアル**（PDF または Markdown）
  - 各ロールごとの操作方法
  - 画面遷移図

- **工夫点・アピール**
  - 実装した機能の工夫
  - 技術的なチャレンジ

- **業務改善提案**
  - 現場の受け入れやすさを考慮した提案
  - 段階的な導入計画

- **感想**
  - 開発を通じて学んだこと
  - 苦労した点と解決方法

## LabAppでの実装アプローチ

### 使用するkits

```python
# kits.accounts - ユーザー・ロール管理
# kits.approvals - 承認フロー（FSM）
# kits.audit - 変更履歴追跡
```

### モデル設計例

```python
class OvertimeRequest(models.Model):
    """残業申請モデル"""

    # 申請者情報
    employee = models.ForeignKey(User, related_name='overtime_requests')

    # 残業情報
    date = models.DateField('残業日')
    start_time = models.TimeField('開始時刻')
    end_time = models.TimeField('終了時刻')
    duration_minutes = models.IntegerField('残業時間（分）')
    reason = models.TextField('理由')

    # 承認フロー（django-fsm）
    status = FSMField(default='draft', max_length=50)
    # draft → submitted → consolidated → approved → confirmed

    # 承認者記録
    consolidator = models.ForeignKey(User, null=True, related_name='consolidated_requests')
    approver = models.ForeignKey(User, null=True, related_name='approved_requests')

    # 履歴管理
    history = HistoricalRecords()
```

### 状態遷移図

```
draft        # 下書き
  ↓
submitted    # 申請済み（次長待ち）
  ↓
consolidated # 取りまとめ完了（課長待ち）
  ↓
approved     # 承認完了
  ↓
confirmed    # 確定（月次処理完了）
```

## 開発のポイント

### 1. 段階的な移行への配慮
- 15分単位と1分単位の並行運用期間を設ける
- 過去データとの互換性を保つ

### 2. 使いやすさ
- 時刻入力のUIを工夫（ドロップダウン + 手入力）
- よく使う理由のテンプレート機能

### 3. 印刷機能
- WeasyPrintを使用したPDF生成
- 印鑑欄など従来の書式との親和性

### 4. 月次処理
- 集計データのCSVエクスポート
- 人事システムへのデータ連携を想定

## 参考情報

### 関連するDjangoパッケージ
- `django-fsm`: 状態管理
- `django-simple-history`: 履歴管理
- `WeasyPrint`: PDF生成
- `django-import-export`: CSV/Excelエクスポート

### セキュリティ考慮事項
- ロールベースのアクセス制御
- 承認後のデータ改ざん防止
- 監査ログの記録
