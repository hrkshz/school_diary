"""
バリデーター

インポートデータのバリデーションを担当します。
"""

import logging
from typing import Any

import pandas as pd
from django.forms import ModelForm

logger = logging.getLogger(__name__)


class ImportValidator:
    """
    インポートバリデーター

    Djangoモデルのバリデーションルールを使用してデータを検証します。
    """

    def __init__(self, model):
        """
        Args:
            model: Djangoモデルクラス
        """
        self.model = model

        # モデルフォームを動的に生成
        self.form_class = type(
            f"{model.__name__}ImportForm",
            (ModelForm,),
            {
                "Meta": type(
                    "Meta",
                    (),
                    {
                        "model": model,
                        "fields": "__all__",
                    },
                ),
            },
        )

    def validate_row(self, row_dict: dict[str, Any]) -> dict[str, list[str]]:
        """
        1行をバリデーション

        Args:
            row_dict: 行データ

        Returns:
            エラー辞書 {'field_name': ['error1', 'error2'], ...}
        """
        form = self.form_class(data=row_dict)

        if form.is_valid():
            return {}

        # エラーを整形
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = [str(e) for e in error_list]

        return errors

    def validate_dataframe(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """
        DataFrame全体をバリデーション

        Args:
            df: pandas DataFrame

        Returns:
            エラーリスト [{'row': 1, 'field': 'name', 'error': '...'}, ...]
        """
        all_errors = []

        for row_num, (_, row) in enumerate(df.iterrows(), start=2):
            row_dict = row.where(pd.notna(row), None).to_dict()
            errors = self.validate_row(row_dict)

            if errors:
                for field, error_messages in errors.items():
                    for error_msg in error_messages:
                        all_errors.append(
                            {
                                "row": row_num,  # ヘッダー行を考慮して start=2
                                "field": field,
                                "error": error_msg,
                            },
                        )

        return all_errors


class CustomValidator:
    """
    カスタムバリデーター

    Djangoモデルのバリデーション以外の検証ロジックを追加できます。
    """

    def __init__(self):
        self.validators = []

    def add_validator(self, field: str, validator_func):
        """
        バリデーターを追加

        Args:
            field: フィールド名
            validator_func: バリデーション関数 (value) -> bool
        """
        self.validators.append((field, validator_func))

    def validate(self, row_dict: dict[str, Any]) -> dict[str, list[str]]:
        """
        カスタムバリデーション実行

        Args:
            row_dict: 行データ

        Returns:
            エラー辞書
        """
        errors = {}

        for field, validator_func in self.validators:
            value = row_dict.get(field)
            try:
                if not validator_func(value):
                    errors.setdefault(field, []).append(f"バリデーションエラー: {field}")
            except Exception as e:
                errors.setdefault(field, []).append(str(e))

        return errors
