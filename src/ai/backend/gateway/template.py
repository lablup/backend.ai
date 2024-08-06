import json
from typing import Any, List, Optional

from jinja2 import nodes
from jinja2.ext import Extension
from jinja2.parser import Parser


class TOMLField(Extension):
    tags = {"toml_field"}

    def parse(self, parser: Parser) -> nodes.Node | List[nodes.Node]:
        tag_name = list(self.tags)[0]
        lineno = parser.stream.expect(f"name:{tag_name}").lineno
        field_name: nodes.Expr = parser.parse_expression()
        field_value: nodes.Expr = parser.parse_expression()
        return nodes.Output(
            [
                nodes.CondExpr(
                    # TOML does not have "null" syntax so let's comment out the field.
                    # We should skip "undefined" field also.
                    nodes.Or(
                        nodes.Test(field_value, "none", [], [], None, None),
                        nodes.Test(field_value, "undefined", [], [], None, None),
                    ),
                    nodes.Concat(
                        [
                            nodes.TemplateData("# "),
                            field_name,
                            nodes.TemplateData(" = "),
                        ],
                        lineno=lineno,
                    ),
                    nodes.Concat(
                        [
                            field_name,
                            nodes.TemplateData(" = "),
                            self._transform(field_value, lineno=lineno),
                        ],
                        lineno=lineno,
                    ),
                ),
            ],
            lineno=lineno,
        )

    def _transform(self, field_value: nodes.Expr, lineno: Optional[int] = None) -> nodes.Expr:
        field_value = nodes.Filter(field_value, "toml_scalar", [], [], None, None, lineno=lineno)
        return field_value


class TOMLStringListField(TOMLField):
    tags = {"toml_strlist_field"}

    def _transform(self, field_value: nodes.Expr, lineno: Optional[int] = None) -> nodes.Expr:
        field_value = nodes.Filter(
            field_value, "join", [nodes.Const(",")], [], None, None, lineno=lineno
        )
        field_value = nodes.Filter(field_value, "toml_scalar", [], [], None, None, lineno=lineno)
        return field_value


def toml_scalar(s: Any) -> str:
    """
    Encodes an arbitry Python object into a TOML-compatible string representation.
    The implementation borrows most of it from `json.dumps()`.

    Note that Jinja's default `tojson` filter uses its own HTML-safe unicode escaping for
    '<', '>', '&', "'" after applying `json.loads()` but we need to avoid doing so.

    ref) https://github.com/pallets/jinja/blob/7fb13bf/src/jinja2/utils.py#L657-L663
    """
    # If our custom tags are used, null values must be handled as commenting out the
    # entire field line and should not be passed to this filter.
    assert s is not None, "null is not allowed as a TOML scalar value"
    return json.dumps(s, ensure_ascii=False)
