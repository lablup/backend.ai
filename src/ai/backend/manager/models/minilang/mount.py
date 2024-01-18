from typing import Mapping

from lark import Lark, Transformer, lexer
from lark.exceptions import LarkError


# https://github.com/lark-parser/lark/blob/master/lark/grammars/common.lark
_grammar = r"""
    start: pair("," pair)*
    pair: key "=" value
    key: SLASH? CNAME (SEPARATOR CNAME)*
    value: SLASH? CNAME (SEPARATOR CNAME)* | ESCAPED_STRING

    SEPARATOR: SLASH | "," | "=" | ":" | "-"
    SLASH: "/"

    %import common.CNAME
    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""


class DictTransformer(Transformer):
    def start(self, pairs: list[tuple[str, str]]) -> dict[str, str]:
        return dict(pairs)

    def pair(self, token: list[str]) -> tuple[str, str]:
        key, value = token
        return (key, value)

    def key(self, token: list[lexer.Token]) -> str:
        return str(token[0])
    
    def value(self, token: list[lexer.Token]) -> str:
        return "".join(token)


_parser = Lark(_grammar, parser="lalr")


class VirtualFolderMountParser:
    def __init__(self) -> None:
        self._parser = _parser

    def parse_mount(self, expr: str) -> Mapping[str, str]:
        # {"source": "abc=zxc", "target": "/home/work"}
        try:
            ast = self._parser.parse(expr)
            result = DictTransformer().transform(ast)
        except LarkError as e:
            raise ValueError(f"Virtual folder mount parsing error: {e}")
        return result
