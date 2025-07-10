import logging
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.errors.exceptions import InternalServerError
from ai.backend.manager.models.keypair import keypairs

from .base import BaseAuthRepository

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class KeypairRepository(BaseAuthRepository):
    async def create_keypair(self, keypair_data: dict) -> None:
        try:
            async with self._db.begin() as conn:
                query = keypairs.insert().values(keypair_data)
                await conn.execute(query)
        except SQLAlchemyError as e:
            log.error("Failed to create keypair: {}", e)
            raise InternalServerError("Database error occurred while creating keypair")

    async def deactivate_user_keypairs(self, user_id: str) -> None:
        async with self._db.begin() as conn:
            query = keypairs.update().values(is_active=False).where(keypairs.c.user_id == user_id)
            await conn.execute(query)

    async def get_ssh_public_key(self, access_key: str) -> Optional[str]:
        async with self._db.begin() as conn:
            query = sa.select([keypairs.c.ssh_public_key]).where(
                keypairs.c.access_key == access_key
            )
            return await conn.scalar(query)

    async def update_ssh_keypair(self, access_key: str, public_key: str, private_key: str) -> None:
        async with self._db.begin() as conn:
            data = {
                "ssh_public_key": public_key,
                "ssh_private_key": private_key,
            }
            query = keypairs.update().values(data).where(keypairs.c.access_key == access_key)
            await conn.execute(query)
