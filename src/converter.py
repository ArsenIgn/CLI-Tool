"""Вычисление констант и построение XML."""

from copy import deepcopy
from xml.etree import ElementTree as xml

from pyparsing import ParseBaseException, col, lineno

from .config_parser import PARSER


class ConfigError(ValueError):
    """Ошибка входной конфигурации."""


def render(node, constants, source):
    """Преобразует узел дерева в элемент XML."""
    kind, contents, *positions = node
    if kind == "reference":
        if contents not in constants:
            position = positions[0]
            line = lineno(position, source)
            column = col(position, source)
            raise ConfigError(
                f"Строка {line}, столбец {column}: "
                f"константа {contents} не объявлена."
            )
        return deepcopy(constants[contents])

    element = xml.Element(kind)
    if kind == "array":
        for child in contents:
            xml.SubElement(element, "item").append(
                render(child, constants, source)
            )
    elif kind == "dict":
        for name, child in contents:
            xml.SubElement(element, "entry", name=name).append(
                render(child, constants, source)
            )
    else:
        element.text = contents
    return element


def convert(source):
    """Разбирает текст и возвращает XML с заголовком UTF-8."""
    try:
        declarations, value = PARSER.parse_string(source, parse_all=True)
    except ParseBaseException as error:
        raise ConfigError(
            f"Строка {error.lineno}, столбец {error.col}: "
            f"синтаксическая ошибка ({error.msg})."
        ) from error

    constants = {}
    for name, node, position in declarations:
        if name in constants:
            line = lineno(position, source)
            column = col(position, source)
            raise ConfigError(
                f"Строка {line}, столбец {column}: "
                f"константа {name} уже объявлена."
            )
        constants[name] = render(node, constants, source)

    root = xml.Element("config")
    root.append(render(value, constants, source))
    xml.indent(root, space="  ")
    return xml.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n"
