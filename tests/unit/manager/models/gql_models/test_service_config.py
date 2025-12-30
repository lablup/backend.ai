from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ai.backend.manager.models.gql_models.service_config import ServiceConfigNode


@pytest.mark.asyncio
async def test_service_config_node_load_returns_dict_not_tuple() -> None:
    """Regression test for BA-3595: unified_config should be dict, not tuple."""
    # Mock ResolveInfo and context
    mock_info = MagicMock()
    mock_config = MagicMock()
    mock_config.model_dump.return_value = {"key": "value"}
    mock_config.model_json_schema.return_value = {"type": "object"}
    mock_info.context.config_provider.config = mock_config

    # Call the method
    result = await ServiceConfigNode.load(mock_info, "manager")

    # Verify configuration is dict, not tuple (BA-3595 regression)
    assert isinstance(result.configuration, dict), (
        f"configuration should be dict, got {type(result.configuration)}"
    )
    assert result.configuration == {"key": "value"}
    assert result.schema == {"type": "object"}
    assert result.service == "manager"
