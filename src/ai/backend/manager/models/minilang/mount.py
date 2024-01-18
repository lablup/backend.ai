from typing import Mapping, TypeAlias

from lark import Lark, Transformer, lexer
from lark.exceptions import LarkError


# https://github.com/lark-parser/lark/blob/master/lark/grammars/common.lark
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

_reserved_keys = frozenset({"type", "source", "target", "perm", "permission"})

_escape_map = {
    "\\,": ",",
    "\\:": ":",
    "\\=": "=",
}


PairType: TypeAlias = tuple[str, str]


class DictTransformer(Transformer):
    def start(self, pairs: list[PairType]) -> dict[str, str]:
        print(f"Transformer.start() {pairs=}")
        if isinstance(pairs[0], list):  # [[("source", "vf-000")]]
            return dict(pairs[0])
        return dict(pairs)
    
    def pair(self, token: list[str, str]) -> PairType:
        print(f"Transformer.pair() {token=}")
        if token[0] not in _reserved_keys:  # vf-000[:/home/work]
            result = [("source", token[0])]
            if (target := token[1]) is not None:
                result.append(("target", target))
            return result
        return (token[0], token[1])
    
    def key(self, token: list[lexer.Token]) -> str:
        print(f"Transformer.key() {token=}")
        # return token
        return "".join(token)
    
    def value(self, token: list[lexer.Token]) -> str:
        # print(f"Transformer.value() {token=}")
        # return token
        result = "".join(token)
        for pair in _escape_map.items():
            result = result.replace(*pair)
        # result = "".join(token).replace("\,", ",")
        print(f"Transformer.value() {token=} -> {result=}")
        return result


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
