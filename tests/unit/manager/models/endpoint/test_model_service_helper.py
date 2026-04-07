"""BA-5620 reproduction matrix.

Verifies the actual behavior of `validate_model_definition_file_exists`
across all combinations of (suggested_path, storage contents).
This pins down what the bug really is and which call sites trigger it.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.common.types import QuotaScopeID, QuotaScopeType, VFolderID
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.endpoint.row import ModelServiceHelper


def _sm() -> MagicMock:
    sm = MagicMock()
    sm.get_proxy_and_volume = MagicMock(return_value=("p", "v"))
    return sm


def _vfid() -> VFolderID:
    return VFolderID(QuotaScopeID(QuotaScopeType.USER, uuid.uuid4()), uuid.uuid4())


async def _call(suggested: str | None, listing: list[str]) -> str:
    with patch.object(
        ModelServiceHelper,
        "_listdir",
        new=AsyncMock(return_value={"items": [{"name": n} for n in listing]}),
    ):
        return await ModelServiceHelper.validate_model_definition_file_exists(
            _sm(), "h", _vfid(), suggested
        )


# === Storage contains ONLY model-definition.yml ===


async def test_yml_only__suggested_none__resolves_yml() -> None:
    """When path is unspecified, helper auto-discovers .yml."""
    assert await _call(None, ["model-definition.yml"]) == "model-definition.yml"


async def test_yml_only__suggested_yaml__resolves_yml_after_fix() -> None:
    """BA-5620: client/WebUI sends 'model-definition.yaml' but only .yml exists.

    Pre-fix: helper raised `InvalidAPIParameters('...model-definition.yaml not found...')`.
    Post-fix: helper falls back to the equivalent .yml extension.
    """
    assert await _call("model-definition.yaml", ["model-definition.yml"]) == "model-definition.yml"


async def test_yml_only__suggested_yml__resolves_yml() -> None:
    assert await _call("model-definition.yml", ["model-definition.yml"]) == "model-definition.yml"


# === Storage contains ONLY model-definition.yaml (mirror case) ===


async def test_yaml_only__suggested_none__resolves_yaml() -> None:
    assert await _call(None, ["model-definition.yaml"]) == "model-definition.yaml"


async def test_yaml_only__suggested_yml__resolves_yaml_after_fix() -> None:
    """Mirror of BA-5620 — symmetric fallback."""
    assert await _call("model-definition.yml", ["model-definition.yaml"]) == "model-definition.yaml"


async def test_yaml_only__suggested_yaml__resolves_yaml() -> None:
    assert (
        await _call("model-definition.yaml", ["model-definition.yaml"]) == "model-definition.yaml"
    )


# === Negative case: neither extension present ===


async def test_neither_present__suggested_yaml__raises() -> None:
    with pytest.raises(InvalidAPIParameters):
        await _call("model-definition.yaml", ["README.md"])


async def test_neither_present__suggested_none__raises() -> None:
    with pytest.raises(InvalidAPIParameters):
        await _call(None, ["README.md"])


# === Custom (non-equivalent) suggested path must still match exactly ===


async def test_custom_path__exact_match__resolves() -> None:
    assert await _call("subdir/spec.yaml", ["spec.yaml"]) == "subdir/spec.yaml"


async def test_custom_path__not_found__raises() -> None:
    with pytest.raises(InvalidAPIParameters):
        await _call("subdir/spec.yaml", ["other.yaml"])
