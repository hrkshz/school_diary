"""
Chart.jsラッパー

Chart.jsのグラフ設定をPythonから簡単に生成するためのヘルパークラス

使用例:
    from kits.reports.charts import ChartBuilder

    # 折れ線グラフ
    chart = ChartBuilder.line(
        labels=['1月', '2月', '3月'],
        datasets=[{'label': '売上', 'data': [100, 200, 150]}],
        title='月次売上推移',
    )
    chart_json = chart.to_json()

    # 棒グラフ
    chart = ChartBuilder.bar(
        labels=['営業', '開発', '総務'],
        datasets=[{'label': '人数', 'data': [10, 20, 5]}],
        title='部門別人数',
    )

    # 円グラフ
    chart = ChartBuilder.pie(
        labels=['営業', '開発', '総務'],
        data=[10, 20, 5],
        title='部門別構成',
    )
"""

import json
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from typing import Any


@dataclass
class ChartDataset:
    """Chart.jsのデータセット"""

    label: str
    data: list[float]
    backgroundColor: list[str] | str | None = None  # noqa: N815
    borderColor: str | None = None  # noqa: N815
    borderWidth: int = 1  # noqa: N815
    fill: bool = False
    tension: float = 0.1  # 曲線の滑らかさ（折れ線グラフ用）

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換（NoneフィールドはJSONに含めない）"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ChartOptions:
    """Chart.jsのオプション"""

    responsive: bool = True
    maintainAspectRatio: bool = True  # noqa: N815
    plugins: dict[str, Any] = field(default_factory=dict)
    scales: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)


class ChartBuilder:
    """
    Chart.jsのグラフ設定を生成するビルダークラス

    Chart.jsのJSON設定をPythonから簡単に生成できます。
    ビルダーパターンを採用しており、メソッドチェーンで設定を積み重ねることができます。

    使用例:
        # メソッドチェーンでの設定
        chart = (
            ChartBuilder('line')
            .set_labels(['1月', '2月', '3月'])
            .add_dataset('売上', [100, 200, 150], border_color='#4F46E5')
            .set_title('月次売上推移')
            .set_y_axis_label('売上額（千円）')
        )
        chart_json = chart.to_json()

        # クラスメソッドでの簡潔な生成
        chart = ChartBuilder.line(
            labels=['1月', '2月', '3月'],
            datasets=[{'label': '売上', 'data': [100, 200, 150]}],
            title='月次売上推移',
        )
        chart_json = chart.to_json()
    """

    def __init__(self, chart_type: str):
        """
        Args:
            chart_type: グラフタイプ ('line', 'bar', 'pie', 'doughnut')
        """
        self.chart_type = chart_type
        self.labels: list[str] = []
        self.datasets: list[ChartDataset] = []
        self.options = ChartOptions()

    def set_labels(self, labels: list[str]) -> "ChartBuilder":
        """
        X軸のラベルを設定

        Args:
            labels: ラベルのリスト

        Returns:
            self（メソッドチェーン用）
        """
        self.labels = labels
        return self

    def add_dataset(
        self,
        label: str,
        data: list[float],
        background_color: list[str] | str | None = None,
        border_color: str | None = None,
        **kwargs,
    ) -> "ChartBuilder":
        """
        データセットを追加

        Args:
            label: データセット名
            data: データのリスト
            background_color: 背景色（単色または色のリスト）
            border_color: 枠線の色
            **kwargs: その他のChartDatasetパラメータ

        Returns:
            self（メソッドチェーン用）
        """
        dataset = ChartDataset(
            label=label,
            data=data,
            backgroundColor=background_color,
            borderColor=border_color,
            **kwargs,
        )
        self.datasets.append(dataset)
        return self

    def set_title(self, title: str) -> "ChartBuilder":
        """
        グラフタイトルを設定

        Args:
            title: タイトル文字列

        Returns:
            self（メソッドチェーン用）
        """
        self.options.plugins["title"] = {
            "display": True,
            "text": title,
            "font": {"size": 16},
        }
        return self

    def set_legend(self, display: bool = True, position: str = "top") -> "ChartBuilder":
        """
        凡例を設定

        Args:
            display: 凡例を表示するか
            position: 凡例の位置 ('top', 'bottom', 'left', 'right')

        Returns:
            self（メソッドチェーン用）
        """
        self.options.plugins["legend"] = {
            "display": display,
            "position": position,
        }
        return self

    def set_y_axis_label(self, label: str) -> "ChartBuilder":
        """
        Y軸ラベルを設定

        Args:
            label: Y軸のラベル文字列

        Returns:
            self（メソッドチェーン用）
        """
        self.options.scales["y"] = {
            "title": {
                "display": True,
                "text": label,
            },
        }
        return self

    def to_dict(self) -> dict[str, Any]:
        """
        辞書形式に変換

        Returns:
            Chart.jsのJSON設定に対応する辞書
        """
        return {
            "type": self.chart_type,
            "data": {
                "labels": self.labels,
                "datasets": [ds.to_dict() for ds in self.datasets],
            },
            "options": self.options.to_dict(),
        }

    def to_json(self, indent: int | None = None) -> str:
        """
        JSON形式に変換

        Args:
            indent: インデント数（Noneの場合は改行なし）

        Returns:
            Chart.jsのJSON設定文字列
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def line(
        cls,
        labels: list[str],
        datasets: list[dict[str, Any]],
        title: str = "",
        y_axis_label: str = "",
    ) -> "ChartBuilder":
        """
        折れ線グラフを作成

        Args:
            labels: X軸のラベル
            datasets: データセットのリスト（各要素は{'label': '名前', 'data': [値]}）
            title: グラフタイトル（オプション）
            y_axis_label: Y軸ラベル（オプション）

        Returns:
            折れ線グラフのChartBuilderインスタンス

        使用例:
            chart = ChartBuilder.line(
                labels=['1月', '2月', '3月'],
                datasets=[
                    {'label': '売上', 'data': [100, 200, 150]},
                    {'label': '利益', 'data': [30, 60, 45]},
                ],
                title='月次推移',
                y_axis_label='金額（千円）',
            )
        """
        builder = cls("line")
        builder.set_labels(labels)

        for ds_data in datasets:
            builder.add_dataset(
                label=ds_data.get("label", ""),
                data=ds_data.get("data", []),
                border_color=ds_data.get("borderColor", "#4F46E5"),
                background_color=None,
                fill=False,
                tension=0.1,
            )

        if title:
            builder.set_title(title)
        if y_axis_label:
            builder.set_y_axis_label(y_axis_label)

        return builder

    @classmethod
    def bar(
        cls,
        labels: list[str],
        datasets: list[dict[str, Any]],
        title: str = "",
        y_axis_label: str = "",
    ) -> "ChartBuilder":
        """
        棒グラフを作成

        Args:
            labels: X軸のラベル
            datasets: データセットのリスト（各要素は{'label': '名前', 'data': [値]}）
            title: グラフタイトル（オプション）
            y_axis_label: Y軸ラベル（オプション）

        Returns:
            棒グラフのChartBuilderインスタンス

        使用例:
            chart = ChartBuilder.bar(
                labels=['営業', '開発', '総務'],
                datasets=[
                    {'label': '正社員', 'data': [10, 20, 5]},
                    {'label': '契約社員', 'data': [2, 5, 1]},
                ],
                title='部門別人数',
            )
        """
        builder = cls("bar")
        builder.set_labels(labels)

        # デフォルトカラーパレット（Tailwind CSS colors）
        colors = [
            "#4F46E5",  # indigo-600
            "#10B981",  # emerald-500
            "#F59E0B",  # amber-500
            "#EF4444",  # red-500
            "#8B5CF6",  # violet-500
            "#06B6D4",  # cyan-500
            "#EC4899",  # pink-500
            "#6366F1",  # indigo-500
        ]

        for idx, ds_data in enumerate(datasets):
            default_color = colors[idx % len(colors)]
            builder.add_dataset(
                label=ds_data.get("label", ""),
                data=ds_data.get("data", []),
                background_color=ds_data.get("backgroundColor", default_color),
                border_color=ds_data.get("borderColor"),
            )

        if title:
            builder.set_title(title)
        if y_axis_label:
            builder.set_y_axis_label(y_axis_label)

        return builder

    @classmethod
    def pie(
        cls,
        labels: list[str],
        data: list[float],
        title: str = "",
        background_colors: list[str] | None = None,
    ) -> "ChartBuilder":
        """
        円グラフを作成

        Args:
            labels: ラベルのリスト
            data: データのリスト
            title: グラフタイトル（オプション）
            background_colors: 背景色のリスト（オプション）

        Returns:
            円グラフのChartBuilderインスタンス

        使用例:
            chart = ChartBuilder.pie(
                labels=['営業', '開発', '総務'],
                data=[10, 20, 5],
                title='部門別構成',
            )
        """
        builder = cls("pie")
        builder.set_labels(labels)

        if not background_colors:
            # デフォルトカラーパレット
            background_colors = [
                "#4F46E5",
                "#10B981",
                "#F59E0B",
                "#EF4444",
                "#8B5CF6",
                "#06B6D4",
                "#EC4899",
                "#6366F1",
            ]

        builder.add_dataset(
            label="",
            data=data,
            background_color=background_colors[: len(data)],
        )

        if title:
            builder.set_title(title)

        return builder

    @classmethod
    def doughnut(
        cls,
        labels: list[str],
        data: list[float],
        title: str = "",
        background_colors: list[str] | None = None,
    ) -> "ChartBuilder":
        """
        ドーナツグラフを作成

        Args:
            labels: ラベルのリスト
            data: データのリスト
            title: グラフタイトル（オプション）
            background_colors: 背景色のリスト（オプション）

        Returns:
            ドーナツグラフのChartBuilderインスタンス

        使用例:
            chart = ChartBuilder.doughnut(
                labels=['営業', '開発', '総務'],
                data=[10, 20, 5],
                title='部門別構成',
            )
        """
        builder = cls("doughnut")
        builder.set_labels(labels)

        if not background_colors:
            # デフォルトカラーパレット
            background_colors = [
                "#4F46E5",
                "#10B981",
                "#F59E0B",
                "#EF4444",
                "#8B5CF6",
                "#06B6D4",
                "#EC4899",
                "#6366F1",
            ]

        builder.add_dataset(
            label="",
            data=data,
            background_color=background_colors[: len(data)],
        )

        if title:
            builder.set_title(title)

        return builder
