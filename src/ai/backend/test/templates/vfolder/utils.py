from uuid import UUID

from ai.backend.client.session import AsyncSession


async def get_vfolder_id_by_name(
    client_session: AsyncSession,
    vfolder_name: str,
) -> UUID:
    vfolder_func = client_session.VFolder(name=vfolder_name)
    await vfolder_func.update_id_by_name()
    if vfolder_func.id is None:
        raise RuntimeError("VFolder id is None.")

    return vfolder_func.id
