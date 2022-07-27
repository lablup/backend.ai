from typing import List

from jinja2 import lexer, nodes
from jinja2.ext import Extension
from jinja2.parser import Parser


class TOMLField(Extension):

    tags = {"toml_field"}

    def parse(self, parser: Parser) -> nodes.Node | List[nodes.Node]:
        tag_name = list(self.tags)[0]
        lineno = parser.stream.expect(f"name:{tag_name}").lineno
        field_name: lexer.Token = parser.stream.expect(lexer.TOKEN_STRING)
        field_value: nodes.Expr = parser.parse_expression()
        return nodes.Output(
            [
                nodes.CondExpr(
                    nodes.Test(field_value, "none", [], [], None, None),
                    # TOML does not have "null" syntax so let's comment out the field.
                    nodes.TemplateData(f"# {field_name.value} ="),
                    nodes.Concat(
                        [
                            nodes.TemplateData(f"{field_name.value} = "),
                            self._transform(field_value),
                        ]
                    ),
                ),
            ],
            lineno=lineno,
        )

    def _transform(self, field_value: nodes.Expr) -> nodes.Expr:
        field_value = nodes.Filter(field_value, "tojson", [], [], None, None)
        field_value = nodes.Filter(field_value, "safe", [], [], None, None)
        return field_value


class TOMLStringListField(TOMLField):

    tags = {"toml_strlist_field"}

    def _transform(self, field_value: nodes.Expr) -> nodes.Expr:
        field_value = nodes.Filter(field_value, "join", [nodes.Const(",")], [], None, None)
        field_value = nodes.Filter(field_value, "tojson", [], [], None, None)
        field_value = nodes.Filter(field_value, "safe", [], [], None, None)
        return field_value
