#!/usr/bin/env python
"""
Kits パッケージドキュメント品質チェックスクリプト

目的: 初心者が超一流のエンジニアの実装をトレースして理解できるか検証

使い方:
    python scripts/check_kits_docs_quality.py notifications
    python scripts/check_kits_docs_quality.py io
    python scripts/check_kits_docs_quality.py {新規パッケージ名}
    python scripts/check_kits_docs_quality.py --all
"""

import sys
from pathlib import Path
from typing import NamedTuple


class DocStats(NamedTuple):
    """ドキュメント統計情報"""

    package_name: str
    file_count: int
    total_lines: int
    total_size_kb: float
    missing_files: list[str]
    files: dict[str, int]  # ファイル名 -> 行数


class QualityResult(NamedTuple):
    """品質チェック結果"""

    package_name: str
    passed: bool
    stats: DocStats
    errors: list[str]
    warnings: list[str]


# 必須ドキュメントファイルと推奨行数（参考値）
REQUIRED_DOCS = {
    "README.md": 200,
    "00_実装ログ.md": 300,  # 実装規模による
    "01_概要と目的.md": 200,  # 具体例が豊富なら長くなる
    "02_設計思想.md": 400,  # 最重要、設計判断の説明が充実すべき
    "03_実装の全体像.md": 300,  # コード構造の複雑さによる
    "05_使い方ガイド.md": 400,  # コード例の数による
    "06_よくある質問.md": 300,  # FAQ数による
    "IMPLEMENTATION_SUMMARY.md": 200,
}

# 品質基準（必須）
MIN_FILE_COUNT = 8  # 必須8ファイル

# 内容チェック用キーワード（02_設計思想.mdで重要）
DESIGN_KEYWORDS = [
    "代替案",
    "トレードオフ",
    "なぜ",
    "理由",
    "検討",
]


def get_docs_dir(package_name: str) -> Path:
    """ドキュメントディレクトリのパスを取得"""
    return Path(__file__).parent.parent / "docs" / "kits" / package_name


def count_lines(file_path: Path) -> int:
    """ファイルの行数をカウント"""
    try:
        with open(file_path, encoding="utf-8") as f:
            return len(f.readlines())
    except Exception:
        return 0


def get_file_size_kb(file_path: Path) -> float:
    """ファイルサイズをKB単位で取得"""
    try:
        return file_path.stat().st_size / 1024
    except Exception:
        return 0.0


def collect_stats(package_name: str) -> DocStats:
    """ドキュメント統計を収集"""
    docs_dir = get_docs_dir(package_name)

    if not docs_dir.exists():
        return DocStats(
            package_name=package_name,
            file_count=0,
            total_lines=0,
            total_size_kb=0.0,
            missing_files=list(REQUIRED_DOCS.keys()),
            files={},
        )

    files = {}
    missing_files = []
    total_lines = 0
    total_size_kb = 0.0

    for required_file in REQUIRED_DOCS:
        file_path = docs_dir / required_file
        if file_path.exists():
            lines = count_lines(file_path)
            size_kb = get_file_size_kb(file_path)
            files[required_file] = lines
            total_lines += lines
            total_size_kb += size_kb
        else:
            missing_files.append(required_file)

    return DocStats(
        package_name=package_name,
        file_count=len(files),
        total_lines=total_lines,
        total_size_kb=total_size_kb,
        missing_files=missing_files,
        files=files,
    )


def check_design_doc_quality(package_name: str) -> list[str]:
    """設計思想ドキュメントの内容チェック"""
    docs_dir = get_docs_dir(package_name)
    design_doc = docs_dir / "02_設計思想.md"

    if not design_doc.exists():
        return ["02_設計思想.md が存在しません"]

    try:
        content = design_doc.read_text(encoding="utf-8")
    except Exception:
        return ["02_設計思想.md を読み込めませんでした"]

    issues = []

    # キーワードチェック
    missing_keywords = []
    for keyword in DESIGN_KEYWORDS:
        if keyword not in content:
            missing_keywords.append(keyword)

    if missing_keywords:
        issues.append(
            f"設計思想に重要なキーワードが不足: {', '.join(missing_keywords)}",
        )

    # 最低限の内容チェック
    if content.count("##") < 5:
        issues.append("設計思想のセクション数が少ない（最低5個推奨）")

    return issues


def check_quality(package_name: str) -> QualityResult:
    """品質チェックを実施（内容重視）"""
    stats = collect_stats(package_name)
    errors = []
    warnings = []

    # 必須ファイルチェック（エラー）
    if stats.missing_files:
        errors.append(f"必須ファイルが不足: {', '.join(stats.missing_files)}")

    # ファイル数チェック（エラー）
    if stats.file_count < MIN_FILE_COUNT:
        errors.append(
            f"ファイル数不足: {stats.file_count}/{MIN_FILE_COUNT}ファイル",
        )

    # 設計思想の内容チェック（エラー）
    design_issues = check_design_doc_quality(package_name)
    if design_issues:
        errors.extend(design_issues)

    # 個別ファイルの行数チェック（警告のみ、参考情報）
    for file_name, recommended_lines in REQUIRED_DOCS.items():
        if file_name in stats.files:
            actual_lines = stats.files[file_name]
            if actual_lines < recommended_lines:
                warnings.append(
                    f"{file_name}: {actual_lines}/{recommended_lines}行（参考値、内容が充実していれば問題なし）",
                )

    passed = len(errors) == 0

    return QualityResult(
        package_name=package_name,
        passed=passed,
        stats=stats,
        errors=errors,
        warnings=warnings,
    )


def print_result(result: QualityResult) -> None:
    """結果を表示"""
    status = "✅ 合格" if result.passed else "❌ 不合格"
    print(f"\n{'=' * 60}")
    print(f"パッケージ: kits.{result.package_name}")
    print(f"ステータス: {status}")
    print(f"{'=' * 60}")

    # 統計情報
    print("\n📊 統計情報:")
    print(f"  ファイル数: {result.stats.file_count}/{MIN_FILE_COUNT}")
    print(f"  総行数: {result.stats.total_lines:,}行（参考値）")
    print(f"  総サイズ: {result.stats.total_size_kb:.1f}KB（参考値）")

    # ファイル詳細
    if result.stats.files:
        print("\n📄 ファイル詳細:")
        for file_name in REQUIRED_DOCS:
            if file_name in result.stats.files:
                lines = result.stats.files[file_name]
                recommended_lines = REQUIRED_DOCS[file_name]
                status_icon = "✅" if lines >= recommended_lines else "ℹ️"
                print(
                    f"  {status_icon} {file_name}: {lines:,}行 (参考値{recommended_lines}行)",
                )
            else:
                print(f"  ❌ {file_name}: 未作成")

    # エラー
    if result.errors:
        print(f"\n❌ エラー ({len(result.errors)}件):")
        for error in result.errors:
            print(f"  • {error}")

    # 警告
    if result.warnings:
        print(f"\n⚠️  警告 ({len(result.warnings)}件):")
        for warning in result.warnings:
            print(f"  • {warning}")

    print()


def print_comparison(results: list[QualityResult]) -> None:
    """複数パッケージの比較表を表示"""
    print("\n" + "=" * 80)
    print("📊 パッケージ比較表")
    print("=" * 80)
    print(
        f"{'パッケージ':<20} {'ファイル数':<10} {'総行数':<15} {'サイズ':<10} {'ステータス':<10}",
    )
    print("-" * 80)

    for result in results:
        status = "✅" if result.passed else "❌"
        print(
            f"kits.{result.package_name:<13} "
            f"{result.stats.file_count:<10} "
            f"{result.stats.total_lines:<15,} "
            f"{result.stats.total_size_kb:<9.1f}KB "
            f"{status}",
        )

    print("-" * 80)
    print(
        f"{'必須基準':<20} {MIN_FILE_COUNT:<10} {'（参考値）':<15} {'（参考値）':<10}",
    )
    print("=" * 80 + "\n")
    print("注: 行数とサイズは参考値です。")
    print("    最重要は「初心者が理解できるか」「設計判断の背景が説明されているか」です。\n")


def main() -> int:
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使い方: python scripts/check_kits_docs_quality.py <package_name>")
        print("        python scripts/check_kits_docs_quality.py --all")
        return 1

    package_arg = sys.argv[1]

    if package_arg == "--all":
        # 全パッケージをチェック
        kits_dir = Path(__file__).parent.parent / "kits"
        packages = [d.name for d in kits_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]

        results = []
        for package in sorted(packages):
            result = check_quality(package)
            results.append(result)
            print_result(result)

        print_comparison(results)

        # 全パッケージが合格しているかチェック
        all_passed = all(r.passed for r in results)
        return 0 if all_passed else 1

    # 単一パッケージをチェック
    result = check_quality(package_arg)
    print_result(result)
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
