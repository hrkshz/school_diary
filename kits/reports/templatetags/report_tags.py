"""
レポート用テンプレートタグ
"""

import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def render_chart(chart_json: str, canvas_id: str = "myChart", height: int = 400) -> str:
    """
    Chart.jsグラフをレンダリング

    使用例:
        {% load report_tags %}
        {% render_chart chart_json "salesChart" 300 %}

    Args:
        chart_json: Chart.js設定（JSON文字列）
        canvas_id: canvas要素のID
        height: グラフの高さ（px）

    Returns:
        HTMLマークアップ
    """
    html = f"""
    <div class="chart-container" style="position: relative; height:{height}px;">
        <canvas id="{canvas_id}"></canvas>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const ctx = document.getElementById('{canvas_id}').getContext('2d');
            const config = {chart_json};
            new Chart(ctx, config);
        }});
    </script>
    """
    return mark_safe(html)


@register.inclusion_tag("reports/partials/data_table.html")
def render_data_table(data, columns=None):
    """
    データテーブルをレンダリング

    使用例:
        {% load report_tags %}
        {% render_data_table data columns %}

    Args:
        data: 辞書のリスト
        columns: 表示するカラムのリスト（Noneの場合は全て）

    Returns:
        テンプレートコンテキスト
    """
    if not data:
        return {"data": [], "columns": []}

    if columns is None:
        columns = list(data[0].keys())

    return {
        "data": data,
        "columns": columns,
    }


@register.filter
def format_number(value, decimals=0):
    """
    数値をフォーマット

    使用例:
        {{ 1234567|format_number }}  → 1,234,567
        {{ 3.14159|format_number:2 }} → 3.14

    Args:
        value: 数値
        decimals: 小数点以下の桁数

    Returns:
        フォーマット済み文字列
    """
    try:
        num = float(value)
        if decimals == 0:
            return f"{int(num):,}"
        return f"{num:,.{decimals}f}"
    except (ValueError, TypeError):
        return value


@register.filter
def to_json(value):
    """
    PythonオブジェクトをJSON文字列に変換

    使用例:
        <script>
            const data = {{ my_dict|to_json }};
        </script>

    Args:
        value: Pythonオブジェクト

    Returns:
        JSON文字列
    """
    return mark_safe(json.dumps(value, ensure_ascii=False))


@register.filter
def get_item(dictionary, key):
    """
    辞書から指定したキーの値を取得

    使用例:
        {{ row|get_item:column }}

    Args:
        dictionary: 辞書オブジェクト
        key: 取得するキー

    Returns:
        キーに対応する値（存在しない場合は空文字列）
    """
    if not isinstance(dictionary, dict):
        return ""
    return dictionary.get(key, "")
