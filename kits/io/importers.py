"""
インポーター層

CSV/TSV/Excelファイルを読み込み、Djangoモデルに保存します。
"""

import logging
from pathlib import Path
from typing import Any

import chardet
import pandas as pd
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import DuplicateStrategy
from .models import ImportHistory
from .models import ImportMapping
from .validators import ImportValidator

logger = logging.getLogger(__name__)


class BaseImporter:
    """
    ベースインポーター

    共通のインポートロジックを提供します。
    """

    def __init__(
        self,
        model_name: str,
        mapping: dict[str, str] | None = None,
        mapping_code: str | None = None,
        unique_fields: list[str] | None = None,
        duplicate_strategy: str = DuplicateStrategy.SKIP,
        encoding: str = "utf-8",
        auto_detect_encoding: bool = True,
        chunk_size: int = 1000,
        validate: bool = True,
        user=None,
    ):
        """
        Args:
            model_name: モデル名（例: "library.Book"）
            mapping: フィールドマッピング {'CSVカラム': 'モデルフィールド'}
            mapping_code: ImportMappingのコード（mappingより優先）
            unique_fields: 重複チェックに使用するフィールド
            duplicate_strategy: 重複時の処理方法
            encoding: 文字コード
            auto_detect_encoding: 文字コード自動検出
            chunk_size: チャンク処理のサイズ
            validate: バリデーション有効化
            user: 実行ユーザー
        """
        self.model_name = model_name
        self.user = user

        # マッピング設定
        if mapping_code:
            mapping_obj = ImportMapping.objects.get(code=mapping_code, is_active=True)
            self.mapping = mapping_obj.field_mapping
            self.unique_fields = mapping_obj.unique_fields
            self.duplicate_strategy = mapping_obj.duplicate_strategy
        else:
            self.mapping = mapping or {}
            self.unique_fields = unique_fields or []
            self.duplicate_strategy = duplicate_strategy

        self.encoding = encoding
        self.auto_detect_encoding = auto_detect_encoding
        self.chunk_size = chunk_size
        self.validate = validate

        # モデルを取得
        try:
            app_label, model_class_name = model_name.split(".")
            self.model = apps.get_model(app_label, model_class_name)
        except (ValueError, LookupError) as e:
            msg = f"モデルが見つかりません: {model_name}"
            raise ValueError(msg) from e

        # バリデーター
        self.validator = ImportValidator(self.model) if validate else None

    def import_file(self, file_path: str | Path) -> ImportHistory:
        """
        ファイルをインポート

        Args:
            file_path: インポートするファイルのパス

        Returns:
            インポート履歴オブジェクト
        """
        file_path = Path(file_path)

        # ImportHistoryを作成
        history = ImportHistory.objects.create(
            model_name=self.model_name,
            original_filename=file_path.name,
            file_size=file_path.stat().st_size,
            encoding=self.encoding,
            imported_by=self.user,
            parameters={
                "mapping": self.mapping,
                "unique_fields": self.unique_fields,
                "duplicate_strategy": self.duplicate_strategy,
            },
        )

        try:
            # 処理開始
            history.mark_as_processing()

            # ファイルを読み込み
            df = self._read_file(file_path)
            history.total_rows = len(df)
            history.save(update_fields=["total_rows"])

            # インポート実行
            result = self._import_dataframe(df, history)

            # 完了としてマーク
            history.mark_as_completed(
                success_count=result["success"],
                failed_count=result["failed"],
                skipped_count=result["skipped"],
                updated_count=result["updated"],
                renumbered_count=result["renumbered"],
            )

            logger.info(f"インポート完了: {history.id} - {result}")
            return history

        except Exception as e:
            # エラーハンドリング
            error_message = str(e)
            history.mark_as_failed(error_message)
            logger.exception(f"インポート失敗: {history.id} - {error_message}")
            raise

    def _read_file(self, _file_path: Path) -> pd.DataFrame:
        """
        ファイルを読み込み（サブクラスでオーバーライド）

        Args:
            _file_path: ファイルパス

        Returns:
            DataFrame
        """
        msg = "サブクラスで実装してください"
        raise NotImplementedError(msg)

    def _import_dataframe(self, df: pd.DataFrame, history: ImportHistory) -> dict[str, int]:
        """
        DataFrameをインポート

        Args:
            df: インポートするDataFrame
            history: インポート履歴

        Returns:
            統計情報 {'success': 100, 'failed': 5, ...}
        """
        stats = {
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "updated": 0,
            "renumbered": 0,
        }

        # マッピングに従ってカラム名を変更
        if self.mapping:
            df = df.rename(columns=self.mapping)

        # チャンク処理
        for chunk_start in range(0, len(df), self.chunk_size):
            chunk_end = min(chunk_start + self.chunk_size, len(df))
            chunk = df.iloc[chunk_start:chunk_end]

            with transaction.atomic():
                for idx, row in chunk.iterrows():
                    try:
                        result = self._import_row(row, idx + 2)  # +2: ヘッダー行 + 0-indexed
                        stats[result] += 1
                    except Exception as e:
                        stats["failed"] += 1
                        history.add_error(idx + 2, "", str(e))

        return stats

    def _import_row(self, row: pd.Series, _row_number: int) -> str:
        """
        1行をインポート

        Args:
            row: 行データ
            row_number: 行番号（エラー表示用）

        Returns:
            'success', 'skipped', 'updated', 'renumbered'のいずれか
        """
        # NaN値をNoneに変換
        row_dict = row.where(pd.notna(row), None).to_dict()

        # バリデーション
        if self.validator:
            errors = self.validator.validate_row(row_dict)
            if errors:
                raise ValidationError(errors)  # type: ignore[arg-type]

        # 重複チェック
        if self.unique_fields:
            lookup = {field: row_dict.get(field) for field in self.unique_fields}
            existing = self.model.objects.filter(**lookup).first()

            if existing:
                return self._handle_duplicate(existing, row_dict)

        # 新規作成
        instance = self.model(**row_dict)
        instance.full_clean()
        instance.save()
        return "success"

    def _handle_duplicate(self, existing, row_dict: dict[str, Any]) -> str:
        """
        重複時の処理

        Args:
            existing: 既存オブジェクト
            row_dict: 新規データ

        Returns:
            'skipped', 'updated', 'renumbered'のいずれか
        """
        if self.duplicate_strategy == DuplicateStrategy.SKIP:
            return "skipped"

        if self.duplicate_strategy == DuplicateStrategy.UPDATE:
            for field, value in row_dict.items():
                setattr(existing, field, value)
            existing.full_clean()
            existing.save()
            return "updated"

        if self.duplicate_strategy == DuplicateStrategy.RENUMBER:
            # 一意フィールドを新規採番
            row_dict = self._renumber_unique_fields(row_dict)
            instance = self.model(**row_dict)
            instance.full_clean()
            instance.save()
            return "renumbered"

        if self.duplicate_strategy == DuplicateStrategy.ERROR:
            msg = f"重複データ: {self.unique_fields}"
            raise ValidationError(msg)

        return "skipped"

    def _renumber_unique_fields(self, row_dict: dict[str, Any]) -> dict[str, Any]:
        """
        一意フィールドを新規採番

        Args:
            row_dict: 行データ

        Returns:
            新規採番された行データ
        """
        # 簡易実装: フィールド値に連番を付加
        for field in self.unique_fields:
            original_value = row_dict.get(field)
            if original_value:
                # 既存の最大番号を取得
                max_obj = (
                    self.model.objects.filter(**{f"{field}__startswith": f"{original_value}_"})
                    .order_by(f"-{field}")
                    .first()
                )

                if max_obj:
                    # 既存の番号から次の番号を生成
                    max_value = getattr(max_obj, field)
                    try:
                        last_number = int(max_value.split("_")[-1])
                        new_number = last_number + 1
                    except (ValueError, IndexError):
                        new_number = 1
                else:
                    new_number = 1

                row_dict[field] = f"{original_value}_{new_number:05d}"

        return row_dict


class CSVImporter(BaseImporter):
    """CSV形式のインポーター"""

    def __init__(self, *args, delimiter: str = ",", **kwargs):
        super().__init__(*args, **kwargs)
        self.delimiter = delimiter

    def _read_file(self, file_path: Path) -> pd.DataFrame:
        """CSVファイルを読み込み"""
        # 文字コード検出
        if self.auto_detect_encoding:
            with open(file_path, "rb") as f:
                result = chardet.detect(f.read())
                detected_encoding = result["encoding"]
                logger.info(
                    f"文字コード検出: {detected_encoding} (confidence: {result['confidence']})",
                )
                encoding = detected_encoding or self.encoding
        else:
            encoding = self.encoding

        # CSV読み込み
        df = pd.read_csv(file_path, encoding=encoding, delimiter=self.delimiter)
        logger.info(f"CSV読み込み完了: {len(df)}行")
        return df


class TSVImporter(CSVImporter):
    """TSV形式のインポーター"""

    def __init__(self, *args, **kwargs):
        kwargs["delimiter"] = "\t"
        super().__init__(*args, **kwargs)


class ExcelImporter(BaseImporter):
    """Excel形式のインポーター"""

    def __init__(self, *args, sheet_name: str | int = 0, **kwargs):
        super().__init__(*args, **kwargs)
        self.sheet_name = sheet_name

    def _read_file(self, file_path: Path) -> pd.DataFrame:
        """Excelファイルを読み込み"""
        df = pd.read_excel(file_path, sheet_name=self.sheet_name, engine="openpyxl")
        logger.info(f"Excel読み込み完了: {len(df)}行")
        return df
