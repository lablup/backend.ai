import asyncio
from uuid import UUID

from ai.backend.client.output.fields import session_node_fields
from ai.backend.client.session import AsyncSession


async def wait_until_all_inference_sessions_ready(
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
        result = await client_session.Service(endpoint_id).info()
        active_routes = result["active_routes"]
        session_ids = [route["session_id"] for route in active_routes]

        ready_session_cnt = 0
        for session_id in session_ids:
            # Wait until all inference sessions are ready.
            if not session_id:
                break
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
            assert session_info["vfolder_mounts"] == [str(vfolder_id)], (
                f"Model vfolder should be mounted into the inference session. "
                f"Actual mounted vfolder: {session_info['vfolder_mounts']}, "
                f"session_id: {session_id}"
            )
            if session_info["status"] == "RUNNING":
                ready_session_cnt += 1

        if ready_session_cnt >= replicas:
            break

        await asyncio.sleep(1)
