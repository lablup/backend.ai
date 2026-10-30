from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final
from unittest.mock import ANY, AsyncMock

import pytest
from etcd_client import ClientError as EtcdClientError

from ai.backend.appproxy.common.config import PermitHashConfig, SecretConfig
from ai.backend.appproxy.common.defs import (
    WORKER_AUTHORITY_LABEL,
    WORKER_HOSTNAME_LABEL,
    WORKER_SERVICE_GROUP,
    WORKER_TLS_LISTEN_LABEL,
)
from ai.backend.appproxy.common.errors.service import (
    WorkerFrontendLabelsInvalid,
    WorkerNotFound,
)
from ai.backend.appproxy.common.etcd import TraefikEtcd
from ai.backend.appproxy.common.types import DigestModType
from ai.backend.appproxy.coordinator.clients.worker.traefik.client import (
    TraefikWorkerClient,
    TraefikWorkerClientArgs,
)
from ai.backend.appproxy.coordinator.clients.worker.traefik.routing_config import (
    TraefikRoutingConfigFactory,
    TraefikRoutingConfigFactoryArgs,
)
from ai.backend.appproxy.coordinator.config import TraefikConfig
from ai.backend.appproxy.coordinator.errors.ingress import (
    TraefikAppliedIngressRevisionInvalidError,
    TraefikIngressRevisionConflictError,
    TraefikIngressWriteFailedError,
)
from ai.backend.common.configs.etcd import EtcdConfig
from ai.backend.common.dto.appproxy.v2.ingress.types import (
    Ingress,
    IngressAccess,
    IngressAccessMode,
    IngressAuthority,
    IngressBackend,
    IngressBackendID,
    IngressFrontend,
    IngressFrontendKind,
    IngressID,
    IngressProtocol,
    IngressTargetGroup,
    IngressTargetGroupID,
    PortFrontend,
)
from ai.backend.common.etcd import NestedStrKeyedMapping
from ai.backend.common.exception import BackendAIError
from ai.backend.common.service_discovery.service_discovery import (
    ServiceDiscovery,
    ServiceEndpoint,
    ServiceMetadata,
)

_MAX_CONCURRENT_ETCD_CALLS: Final[int] = 8
_WORKER_1_WITH_ITS_HOSTNAME_LABELS: Final[dict[str, str]] = {
    WORKER_AUTHORITY_LABEL: "worker-1",
    WORKER_HOSTNAME_LABEL: "worker-1.example.com",
    WORKER_TLS_LISTEN_LABEL: "false",
}


@dataclass(frozen=True)
class _TraefikEtcdAndWorkerState:
    applied_revision_subtrees_by_etcd_prefix: dict[str, NestedStrKeyedMapping] = field(
        default_factory=dict
    )
    revision_etcd_keys_changed_by_another_write: frozenset[str] = frozenset()
    registered_worker_labels: list[dict[str, str]] = field(
        default_factory=lambda: [_WORKER_1_WITH_ITS_HOSTNAME_LABELS]
    )


@dataclass(frozen=True)
class _AcceptedUpsertCase:
    name: str
    state: _TraefikEtcdAndWorkerState
    ingresses: list[Ingress]
    expected_guards: dict[str, str | None]


@dataclass(frozen=True)
class _RejectedUpsertCase:
    name: str
    state: _TraefikEtcdAndWorkerState
    ingresses: list[Ingress]
    expected_error: type[BackendAIError]


@dataclass(frozen=True)
class _PartiallyFailedUpsertCase:
    name: str
    state: _TraefikEtcdAndWorkerState
    ingresses: list[Ingress]
    expected_failed_frontend_keys: list[str]
    expected_guarded_write_attempts: int


@dataclass(frozen=True)
class _TraefikWorkerClientSituation:
    traefik_worker_client: TraefikWorkerClient
    traefik_etcd: AsyncMock
    ingresses: list[Ingress]


def _http_port_ingress_of_worker_1(port: int, revision: int) -> Ingress:
    return Ingress(
        id=IngressID(f"ingress-{port}"),
        authority=IngressAuthority("worker-1"),
        revision=revision,
        frontend=IngressFrontend(
            kind=IngressFrontendKind.PORT,
            protocol=IngressProtocol.HTTP,
            port=PortFrontend(number=port),
        ),
        access=IngressAccess(mode=IngressAccessMode.PUBLIC, allowed_client_ips=[]),
        backend=IngressBackend(
            id=IngressBackendID(f"backend-{port}"),
            target_groups=[
                IngressTargetGroup(id=IngressTargetGroupID("group-1"), weight=1, targets=[])
            ],
        ),
    )


def _worker_service_metadata(labels: dict[str, str]) -> ServiceMetadata:
    return ServiceMetadata.for_endpoint(
        display_name=f"appproxy-worker-{labels[WORKER_AUTHORITY_LABEL]}",
        service_group=WORKER_SERVICE_GROUP,
        version="test",
        endpoint=ServiceEndpoint(
            address="127.0.0.1",
            port=10201,
            protocol="http",
            prometheus_address="127.0.0.1:10201",
        ),
        labels=labels,
    )


@pytest.fixture
def routing_config_factory() -> TraefikRoutingConfigFactory:
    return TraefikRoutingConfigFactory(
        TraefikRoutingConfigFactoryArgs(
            traefik_config=TraefikConfig(
                etcd=EtcdConfig.model_validate({"namespace": "traefik"}), client_ip_strategy=None
            ),
            secrets=SecretConfig(jwt_secret="jwt-secret", api_secret="api-secret"),
            permit_hash=PermitHashConfig(
                secret=b"permit-hash-secret", digest_mod=DigestModType.SHA256
            ),
        )
    )


@pytest.fixture
def upsert_situation(
    case: _AcceptedUpsertCase | _RejectedUpsertCase | _PartiallyFailedUpsertCase,
    routing_config_factory: TraefikRoutingConfigFactory,
) -> _TraefikWorkerClientSituation:
    worker_service_discovery = AsyncMock(spec=ServiceDiscovery)
    if case.state.registered_worker_labels:
        worker_service_discovery.get_service_group.return_value = [
            _worker_service_metadata(labels) for labels in case.state.registered_worker_labels
        ]
    else:
        worker_service_discovery.get_service_group.side_effect = ValueError("No services found")
    traefik_etcd = AsyncMock(spec=TraefikEtcd)
    traefik_etcd.get_prefix.side_effect = (
        lambda etcd_prefix: case.state.applied_revision_subtrees_by_etcd_prefix.get(etcd_prefix, {})
    )
    traefik_etcd.compare_and_replace_prefixes.side_effect = (
        lambda subtrees_by_etcd_prefix, guards: not (
            guards.keys() & case.state.revision_etcd_keys_changed_by_another_write
        )
    )
    return _TraefikWorkerClientSituation(
        traefik_worker_client=TraefikWorkerClient(
            TraefikWorkerClientArgs(
                etcd=traefik_etcd,
                worker_service_discovery=worker_service_discovery,
                routing_config_factory=routing_config_factory,
                max_concurrent_etcd_calls=_MAX_CONCURRENT_ETCD_CALLS,
            )
        ),
        traefik_etcd=traefik_etcd,
        ingresses=case.ingresses,
    )


@pytest.fixture
def removal_of_a_written_ingress(
    routing_config_factory: TraefikRoutingConfigFactory,
) -> _TraefikWorkerClientSituation:
    worker_service_discovery = AsyncMock(spec=ServiceDiscovery)
    worker_service_discovery.get_service_group.return_value = [
        _worker_service_metadata(_WORKER_1_WITH_ITS_HOSTNAME_LABELS)
    ]
    traefik_etcd = AsyncMock(spec=TraefikEtcd)
    traefik_etcd.get.side_effect = {
        "applied_ingress_revisions/worker_worker-1/port-10205/revision": "3"
    }.get
    return _TraefikWorkerClientSituation(
        traefik_worker_client=TraefikWorkerClient(
            TraefikWorkerClientArgs(
                etcd=traefik_etcd,
                worker_service_discovery=worker_service_discovery,
                routing_config_factory=routing_config_factory,
                max_concurrent_etcd_calls=_MAX_CONCURRENT_ETCD_CALLS,
            )
        ),
        traefik_etcd=traefik_etcd,
        ingresses=[_http_port_ingress_of_worker_1(10205, revision=3)],
    )


@pytest.fixture
def removal_of_two_ingresses_with_one_failed_clear(
    routing_config_factory: TraefikRoutingConfigFactory,
) -> _TraefikWorkerClientSituation:
    def fail_to_clear_one_ingress(
        emptied_subtrees_by_etcd_prefix: Mapping[str, NestedStrKeyedMapping],
    ) -> None:
        if (
            "applied_ingress_revisions/worker_worker-1/port-10205/revision"
            in emptied_subtrees_by_etcd_prefix
        ):
            raise EtcdClientError("etcd is unreachable")

    worker_service_discovery = AsyncMock(spec=ServiceDiscovery)
    worker_service_discovery.get_service_group.return_value = [
        _worker_service_metadata(_WORKER_1_WITH_ITS_HOSTNAME_LABELS)
    ]
    traefik_etcd = AsyncMock(spec=TraefikEtcd)
    traefik_etcd.atomic_replace_prefixes.side_effect = fail_to_clear_one_ingress
    return _TraefikWorkerClientSituation(
        traefik_worker_client=TraefikWorkerClient(
            TraefikWorkerClientArgs(
                etcd=traefik_etcd,
                worker_service_discovery=worker_service_discovery,
                routing_config_factory=routing_config_factory,
                max_concurrent_etcd_calls=_MAX_CONCURRENT_ETCD_CALLS,
            )
        ),
        traefik_etcd=traefik_etcd,
        ingresses=[
            _http_port_ingress_of_worker_1(10205, revision=3),
            _http_port_ingress_of_worker_1(10206, revision=5),
        ],
    )


class TestTraefikWorkerClient:
    @pytest.mark.parametrize(
        "case",
        [
            _AcceptedUpsertCase(
                name="no-applied-revision",
                state=_TraefikEtcdAndWorkerState(),
                ingresses=[_http_port_ingress_of_worker_1(10205, revision=3)],
                expected_guards={
                    "applied_ingress_revisions/worker_worker-1/port-10205/revision": None
                },
            ),
            _AcceptedUpsertCase(
                name="older-applied-revision",
                state=_TraefikEtcdAndWorkerState(
                    applied_revision_subtrees_by_etcd_prefix={
                        "applied_ingress_revisions/worker_worker-1/": {
                            "port-10205": {"revision": "2"}
                        }
                    },
                ),
                ingresses=[_http_port_ingress_of_worker_1(10205, revision=3)],
                expected_guards={
                    "applied_ingress_revisions/worker_worker-1/port-10205/revision": "2"
                },
            ),
            _AcceptedUpsertCase(
                name="same-applied-revision",
                state=_TraefikEtcdAndWorkerState(
                    applied_revision_subtrees_by_etcd_prefix={
                        "applied_ingress_revisions/worker_worker-1/": {
                            "port-10205": {"revision": "3"}
                        }
                    },
                ),
                ingresses=[_http_port_ingress_of_worker_1(10205, revision=3)],
                expected_guards={
                    "applied_ingress_revisions/worker_worker-1/port-10205/revision": "3"
                },
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_accepted_upsert_replaces_every_key_of_the_ingress_guarded_by_the_applied_revision(
        self,
        case: _AcceptedUpsertCase,
        upsert_situation: _TraefikWorkerClientSituation,
    ) -> None:
        await upsert_situation.traefik_worker_client.upsert(upsert_situation.ingresses)
        upsert_situation.traefik_etcd.compare_and_replace_prefixes.assert_awaited_once_with(
            {
                "worker_worker-1/http/routers/bai_ingress_port-10205_router": ANY,
                "worker_worker-1/http/services/bai_ingress_port-10205_service": ANY,
                "worker_worker-1/http/middlewares/bai_ingress_port-10205_cors": ANY,
                "worker_worker-1/http/middlewares/bai_ingress_port-10205_ipallowlist": ANY,
                "worker_worker-1/http/middlewares/bai_ingress_port-10205_auth": ANY,
                "worker_worker-1/tcp/routers/bai_ingress_port-10205_router": {},
                "worker_worker-1/tcp/services/bai_ingress_port-10205_service": {},
                "applied_ingress_revisions/worker_worker-1/port-10205/revision": {"": "3"},
            },
            guards=case.expected_guards,
        )

    @pytest.mark.parametrize(
        "case",
        [
            _RejectedUpsertCase(
                name="older-than-applied-revision",
                state=_TraefikEtcdAndWorkerState(
                    applied_revision_subtrees_by_etcd_prefix={
                        "applied_ingress_revisions/worker_worker-1/": {
                            "port-10205": {"revision": "4"}
                        }
                    },
                ),
                ingresses=[_http_port_ingress_of_worker_1(10205, revision=3)],
                expected_error=TraefikIngressRevisionConflictError,
            ),
            _RejectedUpsertCase(
                name="batch-with-one-older-than-applied-revision",
                state=_TraefikEtcdAndWorkerState(
                    applied_revision_subtrees_by_etcd_prefix={
                        "applied_ingress_revisions/worker_worker-1/": {
                            "port-10206": {"revision": "6"}
                        }
                    },
                ),
                ingresses=[
                    _http_port_ingress_of_worker_1(10205, revision=3),
                    _http_port_ingress_of_worker_1(10206, revision=5),
                ],
                expected_error=TraefikIngressRevisionConflictError,
            ),
            _RejectedUpsertCase(
                name="unparsable-applied-revision",
                state=_TraefikEtcdAndWorkerState(
                    applied_revision_subtrees_by_etcd_prefix={
                        "applied_ingress_revisions/worker_worker-1/": {
                            "port-10205": {"revision": "three"}
                        }
                    },
                ),
                ingresses=[_http_port_ingress_of_worker_1(10205, revision=3)],
                expected_error=TraefikAppliedIngressRevisionInvalidError,
            ),
            _RejectedUpsertCase(
                name="no-worker-registered",
                state=_TraefikEtcdAndWorkerState(registered_worker_labels=[]),
                ingresses=[_http_port_ingress_of_worker_1(10205, revision=3)],
                expected_error=WorkerNotFound,
            ),
            _RejectedUpsertCase(
                name="only-another-authority-registered",
                state=_TraefikEtcdAndWorkerState(
                    registered_worker_labels=[
                        {
                            WORKER_AUTHORITY_LABEL: "worker-2",
                            WORKER_HOSTNAME_LABEL: "worker-2.example.com",
                        }
                    ],
                ),
                ingresses=[_http_port_ingress_of_worker_1(10205, revision=3)],
                expected_error=WorkerNotFound,
            ),
            _RejectedUpsertCase(
                name="worker-registered-with-an-unparsable-tls-listen",
                state=_TraefikEtcdAndWorkerState(
                    registered_worker_labels=[
                        {
                            WORKER_AUTHORITY_LABEL: "worker-1",
                            WORKER_HOSTNAME_LABEL: "worker-1.example.com",
                            WORKER_TLS_LISTEN_LABEL: "maybe",
                        }
                    ],
                ),
                ingresses=[_http_port_ingress_of_worker_1(10205, revision=3)],
                expected_error=WorkerFrontendLabelsInvalid,
            ),
            _RejectedUpsertCase(
                name="worker-registered-without-hostname",
                state=_TraefikEtcdAndWorkerState(
                    registered_worker_labels=[{WORKER_AUTHORITY_LABEL: "worker-1"}],
                ),
                ingresses=[_http_port_ingress_of_worker_1(10205, revision=3)],
                expected_error=WorkerNotFound,
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_rejected_upsert_raises_without_writing(
        self,
        case: _RejectedUpsertCase,
        upsert_situation: _TraefikWorkerClientSituation,
    ) -> None:
        with pytest.raises(case.expected_error):
            await upsert_situation.traefik_worker_client.upsert(upsert_situation.ingresses)
        upsert_situation.traefik_etcd.compare_and_replace_prefixes.assert_not_awaited()

    @pytest.mark.parametrize(
        "case",
        [
            _PartiallyFailedUpsertCase(
                name="another-write-commits-first",
                state=_TraefikEtcdAndWorkerState(
                    revision_etcd_keys_changed_by_another_write=frozenset({
                        "applied_ingress_revisions/worker_worker-1/port-10205/revision"
                    }),
                ),
                ingresses=[_http_port_ingress_of_worker_1(10205, revision=3)],
                expected_failed_frontend_keys=["port-10205"],
                expected_guarded_write_attempts=1,
            ),
            _PartiallyFailedUpsertCase(
                name="another-write-commits-first-to-one-of-a-batch",
                state=_TraefikEtcdAndWorkerState(
                    revision_etcd_keys_changed_by_another_write=frozenset({
                        "applied_ingress_revisions/worker_worker-1/port-10205/revision"
                    }),
                ),
                ingresses=[
                    _http_port_ingress_of_worker_1(10205, revision=3),
                    _http_port_ingress_of_worker_1(10206, revision=5),
                ],
                expected_failed_frontend_keys=["port-10205"],
                expected_guarded_write_attempts=2,
            ),
        ],
        ids=lambda case: case.name,
    )
    async def test_upsert_writes_every_ingress_and_reports_the_failed_writes_together(
        self,
        case: _PartiallyFailedUpsertCase,
        upsert_situation: _TraefikWorkerClientSituation,
    ) -> None:
        with pytest.raises(TraefikIngressWriteFailedError) as exc_info:
            await upsert_situation.traefik_worker_client.upsert(upsert_situation.ingresses)
        extra_data = exc_info.value.extra_data
        assert extra_data is not None
        assert [
            failure["frontend_key"] for failure in extra_data["failed_ingresses"]
        ] == case.expected_failed_frontend_keys
        assert (
            upsert_situation.traefik_etcd.compare_and_replace_prefixes.await_count
            == case.expected_guarded_write_attempts
        )

    async def test_removal_of_a_written_ingress_clears_every_key_of_it_and_its_revision(
        self,
        removal_of_a_written_ingress: _TraefikWorkerClientSituation,
    ) -> None:
        await removal_of_a_written_ingress.traefik_worker_client.remove([
            ingress.key() for ingress in removal_of_a_written_ingress.ingresses
        ])
        removal_of_a_written_ingress.traefik_etcd.atomic_replace_prefixes.assert_awaited_once_with({
            "worker_worker-1/http/routers/bai_ingress_port-10205_router": {},
            "worker_worker-1/http/services/bai_ingress_port-10205_service": {},
            "worker_worker-1/http/middlewares/bai_ingress_port-10205_cors": {},
            "worker_worker-1/http/middlewares/bai_ingress_port-10205_ipallowlist": {},
            "worker_worker-1/http/middlewares/bai_ingress_port-10205_auth": {},
            "worker_worker-1/tcp/routers/bai_ingress_port-10205_router": {},
            "worker_worker-1/tcp/services/bai_ingress_port-10205_service": {},
            "applied_ingress_revisions/worker_worker-1/port-10205/revision": {},
        })

    async def test_removal_clears_every_ingress_and_reports_the_failed_clears_together(
        self,
        removal_of_two_ingresses_with_one_failed_clear: _TraefikWorkerClientSituation,
    ) -> None:
        with pytest.raises(TraefikIngressWriteFailedError) as exc_info:
            await removal_of_two_ingresses_with_one_failed_clear.traefik_worker_client.remove([
                ingress.key()
                for ingress in removal_of_two_ingresses_with_one_failed_clear.ingresses
            ])
        extra_data = exc_info.value.extra_data
        assert extra_data is not None
        assert [failure["frontend_key"] for failure in extra_data["failed_ingresses"]] == [
            "port-10205"
        ]
        assert (
            removal_of_two_ingresses_with_one_failed_clear.traefik_etcd.atomic_replace_prefixes.await_count
            == 2
        )
