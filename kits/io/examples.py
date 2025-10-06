"""使用例"""

from django.contrib.auth import get_user_model

from kits.io.importers import CSVImporter
from kits.io.importers import ExcelImporter
from kits.io.models import ImportMapping

User = get_user_model()


def example_1_simple_csv_import():
    """例1: シンプルなCSVインポート"""
    user = User.objects.first()

    importer = CSVImporter(
        model_name="library.Book",
        mapping={
            "タイトル": "title",
            "著者": "author",
            "ISBN": "isbn",
            "価格": "price",
        },
        user=user,
    )

    history = importer.import_file("/path/to/books.csv")
    print(f"インポート完了: {history.success_count}件")


def example_2_with_duplicate_handling():
    """例2: 重複処理付きインポート"""
    user = User.objects.first()

    importer = CSVImporter(
        model_name="library.Book",
        mapping={"ISBN": "isbn", "タイトル": "title"},
        unique_fields=["isbn"],
        duplicate_strategy="update",  # 重複時は更新
        user=user,
    )

    history = importer.import_file("/path/to/books.csv")
    print(f"成功: {history.success_count}, 更新: {history.updated_count}")


def example_3_excel_import_with_renumbering():
    """例3: Excelインポート（新規採番）"""
    # 課題4: 図書館システムでの使用例
    user = User.objects.first()

    importer = ExcelImporter(
        model_name="library.Book",
        mapping={
            "タイトル": "title",
            "バーコードID": "barcode_id",
        },
        unique_fields=["barcode_id"],
        duplicate_strategy="renumber",  # 重複時は新規採番
        sheet_name=0,
        user=user,
    )

    history = importer.import_file("/path/to/school_a_books.xlsx")
    print(f"新規採番: {history.renumbered_count}件")


def example_4_with_mapping_config():
    """例4: マッピング設定を使用"""
    # 事前にImportMappingを作成
    _mapping = ImportMapping.objects.create(
        code="book_import",
        name="図書インポート",
        model_name="library.Book",
        field_mapping={
            "タイトル": "title",
            "著者": "author",
            "ISBN": "isbn",
        },
        unique_fields=["isbn"],
        duplicate_strategy="skip",
    )

    user = User.objects.first()

    # mapping_codeを指定するだけ
    importer = CSVImporter(
        model_name="library.Book",
        mapping_code="book_import",
        user=user,
    )

    history = importer.import_file("/path/to/books.csv")
    print(f"インポート完了: {history.id}")
