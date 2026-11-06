from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.manager.api.gql.user.resolver.query import my_user_v2
from ai.backend.manager.errors.auth import AuthenticationRequired


class TestMyUserV2:
    async def test_call_without_current_user_raises_authentication_required(self) -> None:
        with pytest.raises(AuthenticationRequired):
            await my_user_v2.base_resolver(info=MagicMock())
