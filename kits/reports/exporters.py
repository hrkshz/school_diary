"""
エクスポート機能

DataFrame → PDF/CSV/Excelへの変換を担当

このモジュールは、pandasのDataFrameをさまざまな形式（PDF、CSV、Excel）に
エクスポートする機能を提供します。

使用例:
    from kits.reports.exporters import CSVExporter, ExcelExporter, PDFExporter
    import pandas as pd

    # CSV出力
    df = pd.DataFrame({'名前': ['太郎', '花子'], '年齢': [25, 30]})
    file_size = CSVExporter.export(df, 'output.csv')

    # Excel出力
    file_size = ExcelExporter.export(df, 'output.xlsx', sheet_name='従業員')

    # PDF出力（テンプレートから）
    file_size = PDFExporter.export_from_template(
        'reports/base_report.html',
        {'data': df.to_dict('records')},
        'output.pdf',
    )
"""

import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class CSVExporter:
    """CSV形式でエクスポート"""

    @staticmethod
    def export(df: pd.DataFrame, file_path: str, **kwargs) -> int:
        """
        DataFrameをCSVファイルに出力

        Args:
            df: エクスポートするDataFrame
            file_path: 出力先ファイルパス
            **kwargs: pd.to_csvのオプション

        Returns:
            ファイルサイズ（bytes）

        使用例:
            df = pd.DataFrame({'名前': ['太郎', '花子'], '年齢': [25, 30]})
            file_size = CSVExporter.export(df, 'employees.csv')
        """
        # デフォルト設定
        csv_options = {
            "index": False,
            "encoding": "utf-8-sig",  # Excel対応のBOM付きUTF-8
            **kwargs,
        }

        df.to_csv(file_path, **csv_options)

        file_size = Path(file_path).stat().st_size
        logger.info(f"CSV出力完了: {file_path} ({file_size} bytes)")
        return file_size


class ExcelExporter:
    """Excel形式でエクスポート"""

    @staticmethod
    def export(
        df: pd.DataFrame,
        file_path: str,
        sheet_name: str = "Sheet1",
        include_chart: bool = False,
        chart_config: dict[str, Any] | None = None,
        **kwargs,
    ) -> int:
        """
        DataFrameをExcelファイルに出力

        Args:
            df: エクスポートするDataFrame
            file_path: 出力先ファイルパス
            sheet_name: シート名
            include_chart: グラフを埋め込むか
            chart_config: グラフ設定（xlsxwriter形式）
            **kwargs: pd.to_excelのオプション

        Returns:
            ファイルサイズ（bytes）

        使用例:
            # シンプルなExcel出力
            df = pd.DataFrame({'部門': ['営業', '開発'], '人数': [10, 20]})
            file_size = ExcelExporter.export(df, 'departments.xlsx')

            # グラフ付きExcel出力
            chart_config = {
                'type': 'column',
                'title': '部門別人数',
                'value_columns': ['人数'],
            }
            file_size = ExcelExporter.export(
                df, 'departments.xlsx',
                include_chart=True,
                chart_config=chart_config,
            )
        """
        # xlsxwriterを使用してグラフ付きExcelを生成
        if include_chart and chart_config:
            with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # グラフを追加
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]

                # グラフオブジェクトを作成
                chart = workbook.add_chart({"type": chart_config.get("type", "column")})

                # データ範囲を設定
                row_count = len(df)
                for idx, col in enumerate(df.columns):
                    if col in chart_config.get("value_columns", []):
                        chart.add_series(
                            {
                                "name": col,
                                "categories": [sheet_name, 1, 0, row_count, 0],
                                "values": [sheet_name, 1, idx, row_count, idx],
                            },
                        )

                # グラフを配置
                chart.set_title({"name": chart_config.get("title", "")})
                worksheet.insert_chart("H2", chart)

        else:
            # シンプルなExcel出力
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False, **kwargs)

        file_size = Path(file_path).stat().st_size
        logger.info(f"Excel出力完了: {file_path} ({file_size} bytes)")
        return file_size


class PDFExporter:
    """PDF形式でエクスポート"""

    @staticmethod
    def export(
        html_content: str,
        file_path: str,
        base_url: str | None = None,
    ) -> int:
        """
        HTMLをPDFに変換

        Args:
            html_content: HTML文字列
            file_path: 出力先ファイルパス
            base_url: 相対パスの基準URL

        Returns:
            ファイルサイズ（bytes）

        使用例:
            html = '<html><body><h1>レポート</h1></body></html>'
            file_size = PDFExporter.export(html, 'report.pdf')
        """
        reports_config = getattr(settings, "REPORTS_CONFIG", {})
        pdf_backend = reports_config.get("PDF_BACKEND", "weasyprint")

        if pdf_backend == "weasyprint":
            return PDFExporter._export_weasyprint(html_content, file_path, base_url)
        if pdf_backend == "reportlab":
            return PDFExporter._export_reportlab(html_content, file_path)
        raise ValueError(f"未対応のPDFバックエンド: {pdf_backend}")

    @staticmethod
    def _export_weasyprint(
        html_content: str,
        file_path: str,
        base_url: str | None,
    ) -> int:
        """WeasyPrintでPDF生成"""
        try:
            from weasyprint import HTML
            from weasyprint.text.fonts import FontConfiguration
        except ImportError as e:
            raise ImportError(
                "WeasyPrintがインストールされていません。"
                "pip install weasyprint を実行してください。",
            ) from e

        if base_url is None:
            base_url = getattr(settings, "WEASYPRINT_BASEURL", "")

        # フォント設定
        font_config = FontConfiguration()

        # PDF生成
        html = HTML(string=html_content, base_url=base_url)
        html.write_pdf(
            file_path,
            font_config=font_config,
        )

        file_size = Path(file_path).stat().st_size
        logger.info(f"PDF出力完了（WeasyPrint）: {file_path} ({file_size} bytes)")
        return file_size

    @staticmethod
    def _export_reportlab(html_content: str, file_path: str) -> int:
        """ReportLabでPDF生成（代替）"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import Paragraph
            from reportlab.platypus import SimpleDocTemplate
            from reportlab.platypus import Spacer
        except ImportError as e:
            raise ImportError(
                "ReportLabがインストールされていません。"
                "pip install reportlab を実行してください。",
            ) from e

        # 簡易的なHTML → テキスト変換（本格的にはhtml2textなどを使用）
        text_content = re.sub("<[^<]+?>", "", html_content)

        # PDF生成
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        for line in text_content.split("\n"):
            if line.strip():
                p = Paragraph(line, styles["Normal"])
                story.append(p)
                story.append(Spacer(1, 3 * mm))

        doc.build(story)

        file_size = Path(file_path).stat().st_size
        logger.info(f"PDF出力完了（ReportLab）: {file_path} ({file_size} bytes)")
        return file_size

    @staticmethod
    def export_from_template(
        template_name: str,
        context: dict[str, Any],
        file_path: str,
    ) -> int:
        """
        Djangoテンプレートから直接PDF生成

        Args:
            template_name: テンプレート名
            context: テンプレートコンテキスト
            file_path: 出力先ファイルパス

        Returns:
            ファイルサイズ（bytes）

        使用例:
            context = {
                'title': '月次レポート',
                'data': [{'name': '太郎', 'score': 85}],
                'generated_at': timezone.now(),
            }
            file_size = PDFExporter.export_from_template(
                'reports/monthly_report.html',
                context,
                'monthly_report.pdf',
            )
        """
        # テンプレートをレンダリング
        html_content = render_to_string(template_name, context)

        # PDFに変換
        return PDFExporter.export(html_content, file_path)
