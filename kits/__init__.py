"""kits パッケージ初期化とバージョン読み取り。

- 同ディレクトリの VERSION からバージョン文字列を読む
- 読めない場合は "0.0.0" にフォールバック
"""

from contextlib import suppress
from pathlib import Path

__all__ = ["__version__"]

_DEFAULT_VERSION = "0.0.0"
__version__ = _DEFAULT_VERSION

_version_path = Path(__file__).parent / "VERSION"

# FileNotFound/Permission/IO系は OSError で包括。文字コードは UnicodeDecodeError扱い
with suppress(OSError, UnicodeDecodeError):
    __version__ = _version_path.read_text(encoding="utf-8").strip()
