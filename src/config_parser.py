"""Синтаксический разбор конфигураций варианта №12."""

import pyparsing as pp


def build_parser():
    """Создаёт грамматику и возвращает дерево из помеченных узлов."""
    name = pp.Regex(r"[_A-Z][_a-zA-Z0-9]*")
    value = pp.Forward()
    number = pp.Regex(r"[1-9][0-9]*").set_parse_action(
        lambda tokens: [("number", tokens[0])]
    )
    string = pp.Regex(
        r"'[\x09\x0a\x0d\x20-\x26\x28-\ud7ff\ue000-\ufffd"
        r"\U00010000-\U0010ffff]*'"
    ).set_parse_action(lambda tokens: [("string", tokens[0][1:-1])])
    reference = pp.Regex(r"\$[_A-Z][_a-zA-Z0-9]*\$").set_parse_action(
        lambda source, position, tokens: [
            ("reference", tokens[0][1:-1], position)
        ]
    )
    array = (
        pp.Suppress("({") + pp.Opt(pp.DelimitedList(value)) + pp.Suppress("})")
    ).set_parse_action(lambda tokens: [("array", list(tokens))])
    item = pp.Group(name + pp.Suppress("=") + value)
    dictionary = (
        pp.Suppress(pp.Keyword("dict"))
        + pp.Suppress("(")
        + pp.Opt(pp.DelimitedList(item))
        + pp.Suppress(")")
    ).set_parse_action(lambda tokens: [("dict", list(tokens))])
    value <<= number | string | reference | array | dictionary
    declaration = (
        name + pp.Suppress(pp.Keyword("is")) - value - pp.Suppress(";")
    ).set_parse_action(
        lambda source, position, tokens: [
            (tokens[0], tokens[1], position)
        ]
    )
    return (pp.Group(pp.ZeroOrMore(declaration)) + value).parse_with_tabs()


PARSER = build_parser()
