"""Консольная точка входа конвертера."""

import argparse
from pathlib import Path
import sys

from .converter import ConfigError, convert


def main():
    """Читает стандартный ввод и сохраняет XML по указанному пути."""
    parser = argparse.ArgumentParser(description="Конвертер в XML")
    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="путь к XML-файлу"
    )
    options = parser.parse_args()

    try:
        source = sys.stdin.buffer.read().decode("utf-8-sig")
        result = convert(source)
        options.output.write_bytes(result)
    except (ConfigError, OSError, UnicodeError, RecursionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
