import asyncio
from typing import override
from uuid import UUID

from ai.backend.client.output.fields import keypair_fields, keypair_resource_policy_fields
from ai.backend.client.session import AsyncSession
from ai.backend.test.contexts.auth import KeypairContext
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.model_service import (
    CreatedModelServiceMetaContext,
    ModelServiceContext,
)
from ai.backend.test.templates.model_service.utils import wait_until_all_inference_sessions_ready
from ai.backend.test.templates.template import TestCode

_ENDPOINT_CREATION_TIMEOUT = 30


class ReplicasScaleFailureTooManySessions(TestCode):
    """
    Test case to verify that scaling replicas beyond the maximum allowed sessions fails
    """

    @override
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        model_service_dep = ModelServiceContext.current()
        original_replicas_count = model_service_dep.replicas
        model_service_meta = CreatedModelServiceMetaContext.current()
        endpoint_id = model_service_meta.endpoint_id

        keypair = KeypairContext.current()
        access_key = keypair.access_key
        result = await client_session.KeyPair(access_key).info([keypair_fields["resource_policy"]])
        keypair_resource_policy_name = result["resource_policy"]

        result = await client_session.KeypairResourcePolicy(access_key).info(
            keypair_resource_policy_name,
            [keypair_resource_policy_fields["max_containers_per_session"]],
        )
        # max_containers_per_session = result["max_containers_per_session"]

        vfolder_func = client_session.VFolder(name=model_service_dep.model_vfolder_name)
        await vfolder_func.update_id_by_name()
        if vfolder_func.id is None:
            raise RuntimeError("Model VFolder id is None.")

        # Verify scaling up the replicas
        scaling_up_replicas = original_replicas_count + 2
        await self._verify_replicas_count(
            client_session=client_session,
            endpoint_id=endpoint_id,
            expected_replicas=scaling_up_replicas,
            vfolder_id=vfolder_func.id,
        )

        # Verify scaling down the replicas
        scaling_down_replicas = scaling_up_replicas - 1
        await self._verify_replicas_count(
            client_session=client_session,
            endpoint_id=endpoint_id,
            expected_replicas=scaling_down_replicas,
            vfolder_id=vfolder_func.id,
        )

    async def _verify_replicas_count(
        self,
        client_session: AsyncSession,
        endpoint_id: UUID,
        expected_replicas: int,
        vfolder_id: UUID,
    ) -> None:
        await client_session.Service(id=endpoint_id).scale(expected_replicas)
        await asyncio.wait_for(
            wait_until_all_inference_sessions_ready(
                client_session=client_session,
                endpoint_id=str(endpoint_id),
                replicas=expected_replicas,
                vfolder_id=vfolder_id,
            ),
            timeout=_ENDPOINT_CREATION_TIMEOUT,
        )
        info = await client_session.Service(id=endpoint_id).info()
        assert info["replicas"] == expected_replicas, (
            f"Expected replicas count {expected_replicas}, but got {info['replicas']}."
        )
        assert info["desired_session_count"] == expected_replicas, (
            f"Expected desired session count {expected_replicas}, "
            f"but got {info['desired_session_count']}."
        )
        await client_session.Service(id=endpoint_id).info()
        assert info["replicas"] == expected_replicas, (
            f"Expected replicas count {expected_replicas}, but got {info['replicas']}."
        )
        assert info["desired_session_count"] == expected_replicas, (
            f"Expected desired session count {expected_replicas}, "
            f"but got {info['desired_session_count']}."
        )
