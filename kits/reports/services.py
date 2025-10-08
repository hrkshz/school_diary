"""
レポートサービス層

レポートの生成、データ集計、エクスポートを担当

このモジュールは、レポート生成のビジネスロジックを実装します。
ReportTemplateに基づいてデータを取得し、指定された形式（PDF/CSV/Excel）で
レポートファイルを生成します。

使用例:
    from kits.reports.services import ReportService
    from kits.reports.models import ReportTemplate

    service = ReportService()

    # レポート生成
    template = ReportTemplate.objects.get(code='monthly_overtime')
    report = service.generate_report(
        template=template,
        user=request.user,
        parameters={'date_from': '2024-01-01', 'date_to': '2024-01-31'},
        format='pdf',
    )

    # 期限切れレポートのクリーンアップ
    deleted_count = service.cleanup_expired_reports()
"""

import logging
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import pandas as pd
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from .charts import ChartBuilder
from .exporters import CSVExporter
from .exporters import ExcelExporter
from .exporters import PDFExporter
from .models import Report
from .models import ReportFormat
from .models import ReportStatus
from .models import ReportTemplate

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User
else:
    User = get_user_model()

logger = logging.getLogger(__name__)


class ReportService:
    """
    レポートサービス

    レポートの生成、エクスポート、ファイル管理を行います。

    主な責務:
    - ReportTemplateに基づいたレポート生成
    - データベースクエリの実行
    - データの集計とDataFrame変換
    - Chart.js設定の生成
    - PDF/CSV/Excelへのエクスポート
    - 期限切れレポートのクリーンアップ
    """

    def __init__(self):
        """
        サービスの初期化

        Django設定からREPORTS_CONFIGを読み込み、
        出力ディレクトリと一時ディレクトリを設定します。
        """
        self.config = getattr(settings, "REPORTS_CONFIG", {})
        self.output_dir = Path(self.config.get("OUTPUT_DIR", "media/reports"))
        self.temp_dir = Path(self.config.get("TEMP_DIR", "media/reports/temp"))

        # ディレクトリが存在しない場合は作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        template: ReportTemplate,
        user: User,
        parameters: dict[str, Any] | None = None,
        output_format: str = ReportFormat.PDF,
    ) -> Report:
        """
        レポートを生成

        Args:
            template: レポートテンプレート
            user: 生成者
            parameters: フィルタ条件などのパラメータ
            output_format: 出力形式（'pdf', 'csv', 'xlsx'）

        Returns:
            生成されたレポートオブジェクト

        Raises:
            ValueError: データが見つからない場合
            Exception: レポート生成に失敗した場合

        使用例:
            service = ReportService()
            report = service.generate_report(
                template=template,
                user=request.user,
                parameters={'date_from': '2024-01-01'},
                output_format='pdf',
            )
        """
        if parameters is None:
            parameters = {}

        # Reportオブジェクトを作成
        report = Report.objects.create(
            template=template,
            generated_by=user,
            title=template.name,
            format=output_format,
            parameters=parameters,
            status=ReportStatus.PENDING,
            expires_at=timezone.now()
            + timedelta(days=self.config.get("RETENTION_DAYS", 30)),
        )

        try:
            # ステータスを「生成中」に更新
            report.status = ReportStatus.GENERATING
            report.save(update_fields=["status"])

            # データを取得
            df = self._execute_query(template, parameters)

            if df.empty:
                raise ValueError("データが見つかりませんでした")

            # ファイル名を生成
            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{template.code}_{timestamp}.{output_format}"
            file_path = self.output_dir / filename

            # 形式に応じてエクスポート
            if output_format == ReportFormat.PDF:
                file_size = self._export_pdf(template, df, str(file_path), parameters)
            elif output_format == ReportFormat.CSV:
                file_size = CSVExporter.export(df, str(file_path))
            elif output_format == ReportFormat.XLSX:
                file_size = ExcelExporter.export(df, str(file_path))
            else:
                raise ValueError(f"未対応の形式: {output_format}")

            # 完了としてマーク
            report.mark_as_completed(
                file_path=f"reports/{filename}",
                file_size=file_size,
                row_count=len(df),
            )

            logger.info(f"レポート生成成功: {report.id} - {filename}")
            return report

        except Exception as e:
            # エラーハンドリング
            error_message = str(e)
            report.mark_as_failed(error_message)
            logger.exception(f"レポート生成失敗: {report.id} - {error_message}")
            raise

    def _execute_query(
        self,
        template: ReportTemplate,
        parameters: dict[str, Any],
    ) -> pd.DataFrame:
        """
        クエリを実行してDataFrameを取得

        Args:
            template: レポートテンプレート
            parameters: パラメータ

        Returns:
            DataFrame

        Raises:
            ValueError: モデルが見つからない場合

        注意:
            この実装は簡易版です。本格的な実装では、query_templateを
            安全に実行する仕組み（SQLインジェクション対策など）が必要です。
        """
        if not template.model_name:
            raise ValueError("model_nameが設定されていません")

        # モデルをインポート
        try:
            app_label, model_name = template.model_name.rsplit(".", 1)
            model = apps.get_model(app_label, model_name)
        except (ValueError, LookupError) as e:
            raise ValueError(f"モデルが見つかりません: {template.model_name}") from e

        # QuerySetを取得
        queryset = model.objects.all()

        # パラメータでフィルタ（例: date_from, date_to）
        if "date_from" in parameters:
            queryset = queryset.filter(created_at__gte=parameters["date_from"])
        if "date_to" in parameters:
            queryset = queryset.filter(created_at__lte=parameters["date_to"])

        # DataFrameに変換
        if not queryset.exists():
            return pd.DataFrame()

        return pd.DataFrame(list(queryset.values()))

    def _export_pdf(
        self,
        template: ReportTemplate,
        df: pd.DataFrame,
        file_path: str,
        parameters: dict[str, Any],
    ) -> int:
        """
        PDFとしてエクスポート

        Args:
            template: レポートテンプレート
            df: データ
            file_path: 出力先
            parameters: パラメータ

        Returns:
            ファイルサイズ
        """
        # テンプレートコンテキストを作成
        context = {
            "template": template,
            "parameters": parameters,
            "data": df.to_dict("records"),
            "row_count": len(df),
            "generated_at": timezone.now(),
        }

        # グラフがあれば追加
        if template.chart_config:
            chart_json = self._generate_chart(df, template.chart_config)
            context["chart_json"] = chart_json

        # テンプレートからPDF生成
        html_template = template.html_template or "reports/base_report.html"
        return PDFExporter.export_from_template(html_template, context, file_path)

    def _generate_chart(self, df: pd.DataFrame, chart_config: dict[str, Any]) -> str:
        """
        DataFrameからChart.js設定を生成

        Args:
            df: データ
            chart_config: グラフ設定

        Returns:
            Chart.js JSON文字列

        グラフ設定の例:
            {
                'type': 'bar',
                'x_column': '部門名',
                'y_columns': ['人数', '平均年齢'],
                'title': '部門別統計',
                'y_axis_label': '人数',
            }
        """
        chart_type = chart_config.get("type", "bar")
        x_column = chart_config.get("x_column", df.columns[0])
        y_columns = chart_config.get("y_columns", [df.columns[1]])

        labels = df[x_column].astype(str).tolist()
        datasets = [{"label": y_col, "data": df[y_col].tolist()} for y_col in y_columns]

        # ChartBuilderで生成
        if chart_type == "line":
            chart = ChartBuilder.line(
                labels=labels,
                datasets=datasets,
                title=chart_config.get("title", ""),
                y_axis_label=chart_config.get("y_axis_label", ""),
            )
        elif chart_type == "bar":
            chart = ChartBuilder.bar(
                labels=labels,
                datasets=datasets,
                title=chart_config.get("title", ""),
                y_axis_label=chart_config.get("y_axis_label", ""),
            )
        elif chart_type == "pie":
            # 円グラフは1つのデータセットのみ
            chart = ChartBuilder.pie(
                labels=labels,
                data=df[y_columns[0]].tolist(),
                title=chart_config.get("title", ""),
            )
        else:
            raise ValueError(f"未対応のグラフタイプ: {chart_type}")

        return chart.to_json()

    def cleanup_expired_reports(self) -> int:
        """
        有効期限切れのレポートを削除

        Returns:
            削除件数

        使用例:
            service = ReportService()
            deleted_count = service.cleanup_expired_reports()
            print(f"{deleted_count}件のレポートを削除しました")
        """
        expired_reports = Report.objects.filter(
            expires_at__lt=timezone.now(),
            status=ReportStatus.COMPLETED,
        )

        count = 0
        for report in expired_reports:
            # ファイルを削除
            if report.file:
                file_path = Path(settings.MEDIA_ROOT) / report.file.name
                if file_path.exists():
                    file_path.unlink()

            # DBレコードを削除
            report.delete()
            count += 1

        logger.info(f"期限切れレポートを削除: {count}件")
        return count
