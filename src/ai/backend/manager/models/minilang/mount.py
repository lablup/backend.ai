from typing import Mapping, TypeAlias

from lark import Lark, Transformer, lexer
from lark.exceptions import LarkError


# https://github.com/lark-parser/lark/blob/master/lark/grammars/common.lark
# _grammar = r"""
#     start: pair ("," pair)*
#     # pair: key "=" value
#     pair: pair_v1 | pair_v2
#     pair_v1: vf [":" alias]
#     pair_v2: key "=" value
#     key: SLASH? CNAME (SEPARATOR CNAME)*
#     value: SLASH? CNAME (SEPARATOR CNAME)* | ESCAPED_STRING
#     vf: CNAME (DASH | CNAME | DIGIT)*  # lh
#     alias: SLASH? CNAME (SEPARATOR | CNAME | DIGIT)*

#     SEPARATOR: SLASH | "," | "=" | ":" | DASH
#     SLASH: "/"
#     DASH: "-"

#     %import common.CNAME
#     %import common.DIGIT
#     %import common.ESCAPED_STRING
#     %import common.WS
#     %ignore WS
# """
_grammar = r"""
    start: pair ("," pair)*
    pair: key [("="|":") value]
    key: CNAME (SEPARATOR CNAME)*
    value: SLASH? CNAME (SEPARATOR CNAME)* | ESCAPED_STRING

    # CNAME: ("_"|LETTER) ("_"|LETTER)*
    CNAME: ("_"|LETTER) ("_"|LETTER|DIGIT|DASH)*
    SEPARATOR: SLASH | DASH | "," | "=" | ":"
    SLASH: "/"
    DASH: "-"

    # %import common.CNAME
    %import common.DIGIT
    %import common.LETTER
    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""

_reserved_keys = frozenset({"type", "source", "target", "perm", "permission"})


PairType: TypeAlias = tuple[str, str]


class DictTransformer(Transformer):
    def start(self, pairs: list[PairType]) -> dict[str, str]:
        print(f"Transformer.start() {pairs=}")
        if len(pairs) == 1:
            key, value = pairs[0]
            if key not in _reserved_keys:
                result = {"source": key}
                if value is not None:
                    result["target"] = value
                return result
        return dict(pairs)

    def pair(self, token: list[PairType]) -> PairType:
        print(f"Transformer.pair() {token=}")
        return token

    def key(self, token: list[lexer.Token]) -> str:
        print(f"Transformer.key() {token=}")
        return "".join(token)

    def value(self, token: list[lexer.Token]) -> str:
        print(f"Transformer.value() {token=}")
        return "".join(token)


# class DictTransformer(Transformer):
#     def start(self, pairs: list[tuple[str, str]]) -> dict[str, str]:
#         print(f"Transformer.start() {pairs=} ({type(pairs)=})")
#         # if isinstance(pairs[0], dict.items):
#         #     return dict(pairs[0])
#         if isinstance(pairs[0], list):
#             return dict(pairs[0])
#         return dict(pairs)

#     def pair(self, token: list[tuple[str, str]] | Mapping[str, str | None]):
#         print(f"Transformer.pair() {token=} (type:{type(token)},{type(token[0])})")
#         # return str(token[0])
#         # key, value = token[0]
#         # # return token[0]
#         # return (key, value)
#         if isinstance(token[0], Mapping):
#             return list(token[0].items())
#         return token  # if isinstance(token, list)

#     def pair_v1(self, token: list[lexer.Token]) -> Mapping[str, str | None]:
#         print(f"Transformer.pair_v1() {token=}")
#         result = {"source": token[0]}
#         if alias := token[1]:
#             result["target"] = alias
#         return result

#     def pair_v2(self, token) -> tuple[str, str]:
#         print(f"Transformer.pair_v2() {token=}")
#         # return "".join(token)
#         return tuple(token)

#     def vf(self, token: list[lexer.Token]):
#         print(f"Transformer.vf() {token=}")
#         return "".join(token)

#     def alias(self, token):
#         print(f"Transformer.alias() {token=}")
#         return "".join(token)

#     # def pair(self, token: list[str]) -> tuple[str, str]:
#     #     print(f"Transformer.pair() {token=}")
#     #     key, value = token
#     #     return (key, value)

#     def key(self, token: list[lexer.Token]) -> str:
#         print(f"Transformer.key() {token=}")
#         return str(token[0])

#     def value(self, token: list[lexer.Token]) -> str:
#         print(f"Transformer.value() {token=}")
#         return "".join(token)


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
