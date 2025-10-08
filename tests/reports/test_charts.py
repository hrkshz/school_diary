"""
Chart.jsラッパーのテスト
"""

import json

from django.test import TestCase

from kits.reports.charts import ChartBuilder


class ChartBuilderTestCase(TestCase):
    """ChartBuilderのテスト"""

    def test_line_chart(self):
        """折れ線グラフが生成できる"""
        chart = ChartBuilder.line(
            labels=["1月", "2月", "3月"],
            datasets=[
                {
                    "label": "売上",
                    "data": [100, 200, 150],
                },
            ],
            title="月次売上",
        )

        config = chart.to_dict()
        self.assertEqual(config["type"], "line")
        self.assertEqual(config["data"]["labels"], ["1月", "2月", "3月"])
        self.assertEqual(len(config["data"]["datasets"]), 1)
        self.assertEqual(config["options"]["plugins"]["title"]["text"], "月次売上")

    def test_bar_chart(self):
        """棒グラフが生成できる"""
        chart = ChartBuilder.bar(
            labels=["A", "B", "C"],
            datasets=[
                {
                    "label": "カテゴリ1",
                    "data": [10, 20, 30],
                },
            ],
        )

        config = chart.to_dict()
        self.assertEqual(config["type"], "bar")
        self.assertEqual(len(config["data"]["datasets"]), 1)

    def test_pie_chart(self):
        """円グラフが生成できる"""
        chart = ChartBuilder.pie(
            labels=["Red", "Blue", "Yellow"],
            data=[300, 50, 100],
            title="Color Distribution",
        )

        config = chart.to_dict()
        self.assertEqual(config["type"], "pie")
        self.assertEqual(config["data"]["datasets"][0]["data"], [300, 50, 100])

    def test_chart_to_json(self):
        """JSON変換が正しく動作する"""
        chart = ChartBuilder.bar(
            labels=["A", "B"],
            datasets=[{"label": "Test", "data": [1, 2]}],
        )

        json_str = chart.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["type"], "bar")
