from __future__ import annotations

import yarl
from sqlalchemy.engine.default import DefaultDialect

from ai.backend.manager.models.base import URLColumn
from ai.backend.manager.models.kernel import KernelRow


class TestKernelRowCallbackUrlColumn:
    """
    Regression guard for https://github.com/lablup/backend.ai/issues/11420.

    PR #7880 (BA-3802) replaced the original ``URLColumn`` type on
    ``KernelRow.callback_url`` with plain ``sa.UnicodeText`` while keeping the
    Python annotation ``Mapped[yarl.URL | None]``. Without ``URLColumn``'s
    ``process_bind_param``, asyncpg received a ``yarl.URL`` instance for a
    text parameter and raised ``DataError: expected str, got URL`` on every
    ``POST /session`` carrying a ``callback_url``.
    """

    def test_callback_url_column_uses_url_column_type(self) -> None:
        column_type = KernelRow.__table__.c.callback_url.type
        assert isinstance(column_type, URLColumn), (
            "KernelRow.callback_url must use URLColumn so yarl.URL values are "
            "stringified before reaching asyncpg; got "
            f"{type(column_type).__name__}"
        )

    def test_url_column_stringifies_yarl_url_on_bind(self) -> None:
        url = yarl.URL("http://example.invalid/webhook?token=abc")
        bound = URLColumn().process_bind_param(url, DefaultDialect())
        assert isinstance(bound, str)
        assert bound == str(url)
