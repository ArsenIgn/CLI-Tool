"""Тесты грамматики, констант и консольного интерфейса."""

import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree as xml

from src.converter import ConfigError, convert


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ConverterTests(unittest.TestCase):
    """Проверяет преобразование конфигураций в XML."""

    def test_scalars(self):
        for source, tag, expected in (
            ("12345", "number", "12345"),
            ("'Книга <&>'", "string", "Книга <&>"),
            ("''", "string", ""),
        ):
            with self.subTest(source=source):
                root = xml.fromstring(convert(source))
                self.assertEqual(root.tag, "config")
                self.assertEqual(root[0].tag, tag)
                self.assertEqual(root[0].text or "", expected)

    def test_nested_containers(self):
        root = xml.fromstring(convert("({dict(_x9 = ({dict(A = 7)}))})"))
        self.assertEqual(root.find(".//entry").get("name"), "_x9")
        self.assertEqual(root.findtext(".//entry[@name='A']/number"), "7")

    def test_empty_containers(self):
        root = xml.fromstring(convert("dict(A = ({}), B = dict())"))
        self.assertEqual(len(root.find(".//array")), 0)
        self.assertEqual(len(root.find("./dict/entry/dict")), 0)

    def test_constants_and_repeated_references(self):
        source = "A is 7; B is dict(X = $A$); C is $B$; ({$B$, $C$})"
        root = xml.fromstring(convert(source))
        self.assertEqual(root.findall("./dict"), [])
        values = root.findall("./array/item/dict/entry/number")
        self.assertEqual([value.text for value in values], ["7", "7"])

    def test_invalid_syntax(self):
        for source in (
            "0", "012", "-7", "1.2", "1 2", "dict(a = 1)",
            "dict(A 1)", "({1 2})", "({1,})", "dict(A = 1",
            "'незакрытая строка", "A is 1 2", "A is ; 1",
            "A is 1;", "$ A $", "",
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ConfigError, "синтаксическая"):
                    convert(source)

    def test_invalid_constants(self):
        for source, message in (
            ("dict(A =\n  $X$)", "Строка 2, столбец 3: константа X"),
            ("A is $B$; B is 1; $A$", "B не объявлена"),
            ("A is 1; A is 2; $A$", "A уже объявлена"),
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(ConfigError, message):
                    convert(source)


class CliTests(unittest.TestCase):
    """Запускает CLI с файловым путём и данными на stdin."""

    def run_cli(self, source, *arguments):
        return subprocess.run(
            [sys.executable, "-m", "src.main", *arguments],
            input=source.encode("utf-8"),
            capture_output=True,
            cwd=PROJECT_ROOT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            check=False,
        )

    def test_examples(self):
        for filename, entry, value in (
            ("server.conf", "Port", "8080"),
            ("library.conf", "Days", "21"),
        ):
            with self.subTest(filename=filename), TemporaryDirectory() as tmp:
                output = Path(tmp) / "out file.xml"
                example = PROJECT_ROOT / "examples" / filename
                result = self.run_cli(
                    example.read_text(encoding="utf-8"), "-o", str(output)
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, b"")
                root = xml.parse(output).getroot()
                self.assertEqual(
                    root.findtext(f".//entry[@name='{entry}']/number"),
                    value,
                )

    def test_error_preserves_output(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "existing.xml"
            output.write_bytes(b"previous content")
            result = self.run_cli("dict(A = )", "--output", str(output))
            self.assertEqual(result.returncode, 1)
            self.assertIn("синтаксическая ошибка", result.stderr.decode())
            self.assertEqual(output.read_bytes(), b"previous content")

    def test_missing_output_option(self):
        result = self.run_cli("1")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"--output", result.stderr)
