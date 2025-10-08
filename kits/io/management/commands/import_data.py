"""データインポート管理コマンド"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from kits.io.importers import CSVImporter
from kits.io.importers import ExcelImporter
from kits.io.importers import TSVImporter

User = get_user_model()


class Command(BaseCommand):
    """CSVファイルからデータをインポート"""

    help = "CSVファイルからデータをインポート"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str,
            help="インポートするファイルのパス",
        )
        parser.add_argument(
            "model_name",
            type=str,
            help="モデル名（例: library.Book）",
        )
        parser.add_argument(
            "--format",
            type=str,
            choices=["csv", "tsv", "excel"],
            default="csv",
            help="ファイル形式（デフォルト: csv）",
        )
        parser.add_argument(
            "--mapping",
            type=str,
            help="ImportMappingのコード",
        )
        parser.add_argument(
            "--encoding",
            type=str,
            default="utf-8",
            help="文字コード（デフォルト: utf-8）",
        )
        parser.add_argument(
            "--delimiter",
            type=str,
            default=",",
            help="区切り文字（CSVのみ、デフォルト: ,）",
        )
        parser.add_argument(
            "--sheet",
            type=str,
            default="0",
            help="シート名またはインデックス（Excelのみ、デフォルト: 0）",
        )
        parser.add_argument(
            "--duplicate-strategy",
            type=str,
            choices=["skip", "update", "renumber", "error"],
            default="skip",
            help="重複時の処理（デフォルト: skip）",
        )
        parser.add_argument(
            "--no-validate",
            action="store_true",
            help="バリデーションを無効化",
        )

    def handle(self, *args, **options):
        file_path = options["file_path"]
        model_name = options["model_name"]
        file_format = options["format"]
        mapping_code = options.get("mapping")
        encoding = options["encoding"]
        delimiter = options["delimiter"]
        sheet_name = options["sheet"]
        duplicate_strategy = options["duplicate_strategy"]
        validate = not options["no_validate"]

        # 管理者ユーザーを取得（コマンド実行用）
        user = User.objects.filter(is_superuser=True).first()

        self.stdout.write(self.style.SUCCESS(f"インポート開始: {file_path} → {model_name}"))

        try:
            # インポーター選択
            if file_format == "csv":
                importer = CSVImporter(
                    model_name=model_name,
                    mapping_code=mapping_code,
                    duplicate_strategy=duplicate_strategy,
                    encoding=encoding,
                    delimiter=delimiter,
                    validate=validate,
                    user=user,
                )
            elif file_format == "tsv":
                importer = TSVImporter(
                    model_name=model_name,
                    mapping_code=mapping_code,
                    duplicate_strategy=duplicate_strategy,
                    encoding=encoding,
                    validate=validate,
                    user=user,
                )
            elif file_format == "excel":
                # sheet_nameを整数に変換（可能なら）
                try:
                    sheet_name = int(sheet_name)
                except ValueError:
                    pass  # 文字列のまま（シート名として使用）

                importer = ExcelImporter(
                    model_name=model_name,
                    mapping_code=mapping_code,
                    duplicate_strategy=duplicate_strategy,
                    sheet_name=sheet_name,
                    validate=validate,
                    user=user,
                )
            else:
                msg = f"未対応の形式: {file_format}"
                raise CommandError(msg)

            # インポート実行
            history = importer.import_file(file_path)

            # 結果表示
            self.stdout.write(self.style.SUCCESS(f"\n✅ インポート完了 (ID: {history.id})\n"))
            self.stdout.write(f"ステータス: {history.get_status_display()}")
            self.stdout.write(f"総行数: {history.total_rows}")
            self.stdout.write(f"成功: {history.success_count}")
            self.stdout.write(f"失敗: {history.failed_count}")
            self.stdout.write(f"スキップ: {history.skipped_count}")
            self.stdout.write(f"更新: {history.updated_count}")
            self.stdout.write(f"新規採番: {history.renumbered_count}")
            self.stdout.write(f"成功率: {history.success_rate:.1f}%")

            if history.error_message:
                self.stdout.write(self.style.ERROR(f"\n❌ エラー: {history.error_message}"))

            if history.error_details:
                self.stdout.write(self.style.WARNING("\n⚠️  詳細エラー（最初の5件）:"))
                for error in history.error_details[:5]:
                    self.stdout.write(f"  行{error['row']}: {error['field']} - {error['error']}")

        except Exception as e:
            msg = f"インポート失敗: {e!s}"
            raise CommandError(msg) from e
