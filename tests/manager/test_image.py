from pathlib import Path
import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    selectinload,
    sessionmaker,
)

from ai.backend.common.docker import ImageRef

from ai.backend.manager.models import (
    update_aliases_from_file,
    ImageAliasRow,
    ImageRow,
)
from ai.backend.manager.models.base import metadata as old_metadata
from ai.backend.manager.models.utils import regenerate_table

column_keys = ['nullable', 'index', 'unique', 'primary_key']


@pytest.fixture
async def virtual_image_db():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:', echo=True)
    base = declarative_base()
    metadata = base.metadata

    regenerate_table(old_metadata.tables['images'], metadata)
    regenerate_table(old_metadata.tables['image_aliases'], metadata)
    ImageAliasRow.metadata = metadata
    ImageRow.metadata = metadata
    async_session = sessionmaker(engine, class_=AsyncSession, autoflush=False)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
        await conn.commit()
    async with async_session() as session:
        image_1 = ImageRow(
            'index.docker.io/lablup/test-python:latest', 'x86_64',
            'index.docker.io', 'lablup/test-python', 'latest',
            'sha256:2d577a600afe2d1b38d78bc2ee5abe3bd350890d0652e48096249694e074f9c3',
            123123123, 'COMPUTE', '', {}, {},
        )
        image_1.id = uuid.uuid4()
        image_2 = ImageRow(
            'index.docker.io/lablup/test-python:3.6-debian', 'aarch64',
            'index.docker.io', 'lablup/test-python', '3.6-debian',
            'sha256:2d577a600afe2d1b38d78bc2ee5abe3bd350890d0652e48096249694e074f9c3',
            123123123, 'COMPUTE', '', {}, {},
        )
        image_2.id = uuid.uuid4()
        session.add(image_1)
        session.add(image_2)
        await session.commit()
    yield async_session
    await engine.dispose()


@pytest.fixture
async def image_aliases(tmpdir):
    content = '''
aliases:
  - ['my-python',     'test-python:latest', 'x86_64']
  - ['my-python:3.6', 'test-python:3.6-debian', 'aarch64']  # preferred
'''
    p = Path(tmpdir) / 'test-image-aliases.yml'
    p.write_text(content)

    yield p


@pytest.mark.asyncio
async def test_update_aliases_from_file(virtual_image_db, image_aliases):
    async_session = virtual_image_db
    async with async_session() as session:
        created_aliases = await update_aliases_from_file(session, image_aliases)
        for alias in created_aliases:
            alias.id = uuid.uuid4()
        await session.commit()
        result = await session.execute(
            sa.select(ImageAliasRow).options(selectinload(ImageAliasRow.image)),
        )
        aliases = {}
        for row in result.scalars().all():
            aliases[row.alias] = row.image.image_ref
        assert aliases == {
            'my-python': ImageRef('lablup/test-python:latest', architecture='x86_64'),
            'my-python:3.6': ImageRef('lablup/test-python:3.6-debian', architecture='aarch64'),
        }
