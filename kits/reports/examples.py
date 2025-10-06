"""
使用例
"""

import pandas as pd
from django.contrib.auth import get_user_model

from kits.reports.charts import ChartBuilder
from kits.reports.models import ReportFormat
from kits.reports.models import ReportTemplate
from kits.reports.services import ReportService

User = get_user_model()


def example_1_simple_report():
    """例1: シンプルなレポート生成"""
    # テンプレートを作成
    template, _ = ReportTemplate.objects.get_or_create(
        code="user_list",
        defaults={
            "name": "ユーザー一覧レポート",
            "model_name": "accounts.User",
            "supported_formats": [ReportFormat.CSV, ReportFormat.XLSX],
            "default_format": ReportFormat.CSV,
        },
    )

    # レポートを生成
    user = User.objects.first()
    assert user is not None, "ユーザーが存在しません"

    service = ReportService()
    report = service.generate_report(
        template=template,
        user=user,
        output_format=ReportFormat.CSV,
    )

    print(f"レポート生成完了: {report.file.url}")


def example_2_chart_generation():
    """例2: グラフ生成"""
    # サンプルデータ
    data = {
        "月": ["1月", "2月", "3月", "4月", "5月", "6月"],
        "売上": [120, 190, 300, 250, 200, 310],
        "費用": [80, 100, 150, 120, 90, 180],
    }
    df = pd.DataFrame(data)

    # 折れ線グラフを生成
    chart = ChartBuilder.line(
        labels=df["月"].tolist(),
        datasets=[
            {"label": "売上", "data": df["売上"].tolist()},
            {"label": "費用", "data": df["費用"].tolist()},
        ],
        title="月次売上・費用推移",
        y_axis_label="金額（万円）",
    )

    print("Chart.js設定:")
    print(chart.to_json(indent=2))


def example_3_pdf_report():
    """例3: PDF付きグラフレポート"""
    # グラフ付きテンプレートを作成
    template, _ = ReportTemplate.objects.get_or_create(
        code="monthly_sales_report",
        defaults={
            "name": "月次売上レポート",
            "model_name": "demos.SalesRecord",
            "supported_formats": [ReportFormat.PDF],
            "default_format": ReportFormat.PDF,
            "html_template": "reports/base_report.html",
            "chart_config": {
                "type": "line",
                "x_column": "month",
                "y_columns": ["amount"],
                "title": "月次売上推移",
                "y_axis_label": "売上（円）",
            },
        },
    )

    # レポート生成
    user = User.objects.first()
    assert user is not None, "ユーザーが存在しません"

    service = ReportService()
    report = service.generate_report(
        template=template,
        user=user,
        output_format=ReportFormat.PDF,
        parameters={
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    print(f"PDFレポート生成完了: {report.file.url}")
