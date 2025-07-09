import asyncio
from uuid import UUID

from ai.backend.client.output.fields import service_fields, session_node_fields
from ai.backend.client.session import AsyncSession


# TODO: Remove the polling loop below after the SSE API is added to the model service API
async def ensure_inference_sessions_ready(
    client_session: AsyncSession,
    endpoint_id: UUID,
    replicas: int,
    vfolder_id: UUID,
) -> None:
    """
    Poll the service endpoint until every backing inference-session is RUNNING
    and has the model vfolder mounted.
    """
    while True:
        result = await client_session.Service.detail(
            service_id=str(endpoint_id),
            fields=[
                service_fields["routings"],
            ],
        )
        routings_info = result["routings"]
        healthy_session_ids = []
        for routing in routings_info:
            if routing["session"] is not None and routing["status"] == "HEALTHY":
                healthy_session_ids.append(routing["session"])

        if len(healthy_session_ids) != replicas:
            await asyncio.sleep(1)
            continue

        for session_id in healthy_session_ids:
            session_info = await client_session.ComputeSession.from_session_id(
                UUID(session_id)
            ).detail([
                session_node_fields["type"],
                session_node_fields["status"],
                session_node_fields["vfolder_mounts"],
            ])

            assert session_info["type"] == "inference", (
                f"Session type should be 'inference'. "
                f"Actual type: {session_info['type']}, session_id: {session_id}"
            )
            assert str(vfolder_id) in session_info["vfolder_mounts"], (
                f"Model vfolder should be mounted into the inference session. "
                f"Actual mounted vfolder: {session_info['vfolder_mounts']}, "
                f"session_id: {session_id}"
            )
            assert session_info["status"] == "RUNNING", (
                f"Session should be in RUNNING state. "
                f"Actual status: {session_info['status']}, session_id: {session_id}"
            )
        break
