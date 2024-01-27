from typing import Annotated, Mapping, Sequence, TypeAlias

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
    reserved_keys = frozenset({"type", "source", "target", "perm", "permission"})

    def start(self, pairs: Sequence[PairType]) -> Mapping[str, str]:
        if pairs[0][0] not in self.reserved_keys:  # [["vf-000", "/home/work"]]
            result = {"source": pairs[0][0]}
            if target := pairs[0][1]:
                result["target"] = target
            return result
        return dict(pairs)  # [("type", "bind"), ("source", "vf-000"), ...]

    def pair(self, token: Annotated[Sequence[str], 2]) -> PairType:
        return (token[0], token[1])

    def key(self, token: list[lexer.Token]) -> str:
        return "".join(token)

    def value(self, token: list[lexer.Token]) -> str:
        return "".join(token)


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
