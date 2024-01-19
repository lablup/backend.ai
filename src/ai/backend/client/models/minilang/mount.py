from typing import Mapping, TypeAlias

from lark import Lark, Transformer, lexer
from lark.exceptions import LarkError

_grammar = r"""
    start: pair ("," pair)*
    pair: key [("="|":") value]
    key: SLASH? CNAME (SEPARATOR|CNAME|DIGIT)*
    value: SLASH? CNAME (SEPARATOR|CNAME|DIGIT)* | ESCAPED_STRING

    SEPARATOR: SLASH | "\\," | "\\=" | "\\:" | DASH
    SLASH: "/"
    DASH: "-"

    %import common.CNAME
    %import common.DIGIT
    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""

PairType: TypeAlias = tuple[str, str]


class DictTransformer(Transformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._escape_map = {
            "\\,": ",",
            "\\:": ":",
            "\\=": "=",
        }
        self._reserved_keys = frozenset({"type", "source", "target", "perm", "permission"})

    def start(self, pairs: list[PairType]) -> Mapping[str, str]:
        if isinstance(pairs[0], list):  # [[("source", "vf-000")]]
            return dict(pairs[0])
        return dict(pairs)

    def pair(self, token: list[str, str]) -> PairType:
        if token[0] not in self._reserved_keys:  # vf-000[:/home/work]
            result = [("source", token[0])]
            if (target := token[1]) is not None:
                result.append(("target", target))
            return result
        return (token[0], token[1])

    def key(self, token: list[lexer.Token]) -> str:
        return "".join(token)

    def value(self, token: list[lexer.Token]) -> str:
        result = "".join(token)
        for pair in self._escape_map.items():
            result = result.replace(*pair)
        return result


_parser = Lark(_grammar, parser="lalr")


class MountPointParser:
    def __init__(self) -> None:
        self._parser = _parser

    def parse_mount(self, expr: str) -> Mapping[str, str]:
        try:
            ast = self._parser.parse(expr)
            result = DictTransformer().transform(ast)
        except LarkError as e:
            raise ValueError(f"Virtual folder mount parsing error: {e}")
        return result
