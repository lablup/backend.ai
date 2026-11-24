from collections.abc import Callable

type Lint = Callable[[str, str], list[tuple[int, str]]]

APPPROXY_MODEL = "src/ai/backend/appproxy/coordinator/models/circuit.py"


class TestAppProxyNativeEnumRule:
    def test_enum_type_column_fails(self, lint: Lint) -> None:
        source = """
            class CircuitRow(Base):
                protocol: Mapped[ProxyProtocol] = mapped_column(EnumType(ProxyProtocol))
        """
        assert lint(APPPROXY_MODEL, source) == [(3, "BAI404")]

    def test_enum_type_in_array_column_fails(self, lint: Lint) -> None:
        source = """
            class WorkerRow(Base):
                modes: Mapped[list[AppMode]] = mapped_column(pgsql.ARRAY(EnumType(AppMode)))
        """
        assert lint(APPPROXY_MODEL, source) == [(3, "BAI404")]

    def test_sqlalchemy_enum_column_fails(self, lint: Lint) -> None:
        source = """
            import sqlalchemy as sa
            from sqlalchemy import Enum as SAEnum
            from sqlalchemy.dialects import postgresql

            table = sa.Table(
                "circuits",
                metadata,
                sa.Column("protocol", sa.Enum(ProxyProtocol)),
                sa.Column("app_mode", postgresql.ENUM("http", "tcp", name="appmode")),
                sa.Column("frontend_mode", SAEnum(FrontendMode)),
            )
        """
        assert lint(APPPROXY_MODEL, source) == [(9, "BAI404"), (10, "BAI404"), (11, "BAI404")]

    def test_str_enum_type_column_passes(self, lint: Lint) -> None:
        source = """
            class CircuitRow(Base):
                protocol: Mapped[ProxyProtocol] = mapped_column(
                    StrEnumType(ProxyProtocol, use_name=True), nullable=False
                )
        """
        assert lint(APPPROXY_MODEL, source) == []

    def test_enum_type_outside_column_passes(self, lint: Lint) -> None:
        source = """
            class EnumType(TypeDecorator):
                def copy(self, **kw: Any) -> EnumType:
                    return EnumType(self._enum_cls, **self._opts)
        """
        assert lint("src/ai/backend/appproxy/coordinator/models/base.py", source) == []

    def test_enum_type_column_outside_appproxy_passes(self, lint: Lint) -> None:
        source = """
            class SessionRow(Base):
                status: Mapped[SessionStatus] = mapped_column(EnumType(SessionStatus))
        """
        assert lint("src/ai/backend/manager/models/session/row.py", source) == []
