"""The compute cluster adapter: the search reads both paging modes it advertises, and the
kubeconfig is passed down but never returned."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.common.dto.manager.v2.compute_cluster.request import (
    CreateComputeClusterInput,
    SearchComputeClustersInput,
    UpdateComputeClusterInput,
)
from ai.backend.manager.actions.v2.ops.result import (
    BatchOpsResult,
    CreatedEntityOpsResult,
    EntityOpsResult,
)
from ai.backend.manager.api.adapter_options.cursor.cursor import encode_cursor
from ai.backend.manager.api.adapters.compute_cluster.adapter import ComputeClusterAdapter
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData, ComputeClusterStatus
from ai.backend.manager.errors.api import InvalidGraphQLParameters
from ai.backend.manager.models.specs.pagination import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
)
from ai.backend.manager.secret.types import SecretValue

_KUBECONFIG = """\
apiVersion: v1
kind: Config
clusters:
- name: k8s-a
  cluster:
    server: https://10.0.0.1:6443
    certificate-authority-data: Y2E=
users:
- name: manager
  user:
    token: secret-token
contexts:
- name: k8s-a
  context:
    cluster: k8s-a
    user: manager
current-context: k8s-a
"""


@pytest.fixture
def cluster_data() -> ComputeClusterData:
    now = datetime.now(UTC)
    return ComputeClusterData(
        id=ComputeClusterID(uuid4()),
        name="k8s-a",
        description=None,
        api_server="https://10.0.0.1:6443",
        kubeconfig=SecretValue(_KUBECONFIG),
        namespace_prefix="bai-",
        gateway_addr=None,
        gateway_public_key=None,
        status=ComputeClusterStatus.UNKNOWN,
        status_changed_at=None,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def processors(cluster_data: ComputeClusterData) -> MagicMock:
    processors = MagicMock()
    processors.global_search.run = AsyncMock(
        return_value=BatchOpsResult(
            items=[], total_count=0, has_next_page=False, has_previous_page=False
        )
    )
    processors.create.run = AsyncMock(return_value=CreatedEntityOpsResult(data=cluster_data))
    processors.update.run = AsyncMock(return_value=EntityOpsResult(data=cluster_data))
    return processors


@pytest.fixture
def adapter(processors: MagicMock) -> ComputeClusterAdapter:
    return ComputeClusterAdapter(processors)


@dataclass(frozen=True)
class _CursorCase:
    input: SearchComputeClustersInput
    pagination_type: type[CursorForwardPagination | CursorBackwardPagination]


@pytest.mark.parametrize(
    "case",
    [
        _CursorCase(
            input=SearchComputeClustersInput(first=5, after=encode_cursor(uuid4())),
            pagination_type=CursorForwardPagination,
        ),
        _CursorCase(
            input=SearchComputeClustersInput(last=5, before=encode_cursor(uuid4())),
            pagination_type=CursorBackwardPagination,
        ),
    ],
    ids=lambda case: case.pagination_type.__name__,
)
async def test_search_pages_by_the_cursor_it_is_given(
    case: _CursorCase,
    adapter: ComputeClusterAdapter,
    processors: MagicMock,
) -> None:
    await adapter.global_search(case.input)

    pagination = processors.global_search.run.call_args.args[0].searcher.searcher.pagination
    assert isinstance(pagination, (CursorForwardPagination, CursorBackwardPagination))
    assert type(pagination) is case.pagination_type
    assert pagination.cursor_condition is not None


@dataclass(frozen=True)
class _OffsetCase:
    input: SearchComputeClustersInput
    expected: OffsetPagination


@pytest.mark.parametrize(
    "case",
    [
        _OffsetCase(
            input=SearchComputeClustersInput(limit=3, offset=2),
            expected=OffsetPagination(limit=3, offset=2),
        ),
        _OffsetCase(
            input=SearchComputeClustersInput(offset=2),
            expected=OffsetPagination(limit=50, offset=2),
        ),
        _OffsetCase(
            input=SearchComputeClustersInput(),
            expected=OffsetPagination(limit=50, offset=0),
        ),
    ],
    ids=lambda case: f"limit-{case.expected.limit}-offset-{case.expected.offset}",
)
async def test_search_pages_by_offset(
    case: _OffsetCase,
    adapter: ComputeClusterAdapter,
    processors: MagicMock,
) -> None:
    await adapter.global_search(case.input)

    pagination = processors.global_search.run.call_args.args[0].searcher.searcher.pagination
    assert pagination == case.expected


async def test_search_refuses_two_pagination_modes(
    adapter: ComputeClusterAdapter,
    processors: MagicMock,
) -> None:
    with pytest.raises(InvalidGraphQLParameters):
        await adapter.global_search(SearchComputeClustersInput(first=1, limit=1))

    processors.global_search.run.assert_not_awaited()


async def test_create_passes_the_kubeconfig_down_and_returns_none_of_it(
    adapter: ComputeClusterAdapter,
    processors: MagicMock,
) -> None:
    payload = await adapter.create(
        CreateComputeClusterInput(
            name="k8s-a", api_server="https://10.0.0.1:6443", kubeconfig=_KUBECONFIG
        )
    )

    assert processors.create.run.call_args.args[0].kubeconfig == _KUBECONFIG
    assert "kubeconfig" not in payload.model_dump()
    assert _KUBECONFIG not in payload.model_dump_json()


async def test_update_carries_the_kubeconfig_beside_the_updater(
    adapter: ComputeClusterAdapter,
    processors: MagicMock,
    cluster_data: ComputeClusterData,
) -> None:
    payload = await adapter.update(
        cluster_data.id, UpdateComputeClusterInput(kubeconfig=_KUBECONFIG)
    )

    action = processors.update.run.call_args.args[0]
    assert action.kubeconfig.optional_value() == _KUBECONFIG
    assert action.updater.kubeconfig.optional_value() is None
    assert "kubeconfig" not in payload.model_dump()
