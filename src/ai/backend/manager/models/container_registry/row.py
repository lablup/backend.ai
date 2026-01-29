from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self, cast
from urllib.parse import urlparse

import sqlalchemy as sa
import yarl
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, foreign, load_only, mapped_column, relationship

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.exception import UnknownImageRegistry
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.data.container_registry.types import ContainerRegistryData
from ai.backend.manager.errors.container_registry import (
    InvalidContainerRegistryProject,
    InvalidContainerRegistryURL,
)
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.association_container_registries_groups import (
        AssociationContainerRegistriesGroupsRow,
    )
    from ai.backend.manager.models.image import ImageRow

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore

__all__: Sequence[str] = (
    "ContainerRegistryRow",
    "ContainerRegistryValidator",
    "ContainerRegistryValidatorArgs",
)


@dataclass
class ContainerRegistryValidatorArgs:
    url: str
    type: ContainerRegistryType
    project: str | None


# TODO: Refactor this using inheritance
class ContainerRegistryValidator:
    """
    Validator for container registry configuration.
    """

    _url: str
    _type: ContainerRegistryType
    _project: str | None

    def __init__(self, args: ContainerRegistryValidatorArgs) -> None:
        self._url = args.url
        self._type = args.type
        self._project = args.project

    def _is_valid_url(self, url: str) -> bool:
        try:
            url = url.strip()
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "http://" + url
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def validate(self) -> None:
        """
        Validate container registry configuration.
        """
        # Validate URL format
        if not self._is_valid_url(self._url):
            raise InvalidContainerRegistryURL(f"Invalid URL format: {self._url}")

        # Validate project name for Harbor
        match self._type:
            case ContainerRegistryType.HARBOR | ContainerRegistryType.HARBOR2:
                if self._project is None:
                    raise InvalidContainerRegistryProject("Project name is required for Harbor.")
                if not (1 <= len(self._project) <= 255):
                    raise InvalidContainerRegistryProject("Invalid project name length.")
                pattern = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
                if not pattern.match(self._project):
                    raise InvalidContainerRegistryProject("Invalid project name format.")
            case _:
                pass


def _get_image_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.image import ImageRow

    return ContainerRegistryRow.id == foreign(ImageRow.registry_id)


def _get_association_join_condition() -> sa.ColumnElement[bool]:
    from ai.backend.manager.models.association_container_registries_groups import (
        AssociationContainerRegistriesGroupsRow,
    )

    return ContainerRegistryRow.id == foreign(AssociationContainerRegistriesGroupsRow.registry_id)


class ContainerRegistryRow(Base):
    __tablename__ = "container_registries"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    url: Mapped[str] = mapped_column("url", sa.String(length=512), index=True, nullable=False)
    registry_name: Mapped[str] = mapped_column(
        "registry_name", sa.String(length=255), index=True, nullable=False
    )
    type: Mapped[ContainerRegistryType] = mapped_column(
        "type",
        StrEnumType(ContainerRegistryType),
        default=ContainerRegistryType.DOCKER,
        server_default=ContainerRegistryType.DOCKER,
        nullable=False,
        index=True,
    )
    project: Mapped[str | None] = mapped_column(
        "project", sa.String(length=255), index=True, nullable=True
    )
    username: Mapped[str | None] = mapped_column("username", sa.String(length=255), nullable=True)
    password: Mapped[str | None] = mapped_column("password", sa.String, nullable=True)
    ssl_verify: Mapped[bool | None] = mapped_column(
        "ssl_verify", sa.Boolean, nullable=True, server_default=sa.text("true"), index=True
    )
    is_global: Mapped[bool | None] = mapped_column(
        "is_global", sa.Boolean, nullable=True, server_default=sa.text("true"), index=True
    )
    extra: Mapped[dict[str, Any] | None] = mapped_column(
        "extra", sa.JSON, nullable=True, default=None
    )

    image_rows: Mapped[list[ImageRow]] = relationship(
        "ImageRow",
        back_populates="registry_row",
        primaryjoin=_get_image_join_condition,
    )

    association_container_registries_groups_rows: Mapped[
        list[AssociationContainerRegistriesGroupsRow]
    ] = relationship(
        "AssociationContainerRegistriesGroupsRow",
        back_populates="container_registry_row",
        primaryjoin=_get_association_join_condition,
    )

    def __init__(
        self,
        id: uuid.UUID,
        url: str,
        registry_name: str,
        type: ContainerRegistryType,
        project: str | None = None,
        username: str | None = None,
        password: str | None = None,
        ssl_verify: bool | None = None,
        is_global: bool | None = None,
        extra: dict | None = None,
    ) -> None:
        self.id = id
        self.url = url
        self.registry_name = registry_name
        self.type = type
        self.project = project
        self.username = username
        self.password = password
        self.ssl_verify = ssl_verify
        self.is_global = is_global
        self.extra = extra

    @classmethod
    async def get(
        cls,
        session: AsyncSession,
        id: str | uuid.UUID,
    ) -> ContainerRegistryRow:
        query = sa.select(ContainerRegistryRow).where(ContainerRegistryRow.id == id)
        result = await session.execute(query)
        row = result.scalar()
        if row is None:
            raise NoResultFound
        return row

    @classmethod
    async def list_by_registry_name(
        cls,
        session: AsyncSession,
        registry_name: str,
    ) -> Sequence[ContainerRegistryRow]:
        query = sa.select(ContainerRegistryRow).where(
            ContainerRegistryRow.registry_name == registry_name
        )
        result = await session.execute(query)
        rows = result.scalars().all()
        if not rows:
            raise NoResultFound
        return rows

    @classmethod
    async def get_container_registry_info(
        cls, session: AsyncSession, registry_id: uuid.UUID
    ) -> tuple[yarl.URL, dict]:
        query_stmt = (
            sa.select(ContainerRegistryRow)
            .where(ContainerRegistryRow.id == registry_id)
            .options(
                load_only(
                    ContainerRegistryRow.url,
                    ContainerRegistryRow.username,
                    ContainerRegistryRow.password,
                )
            )
        )
        registry_row = cast(ContainerRegistryRow | None, await session.scalar(query_stmt))
        if registry_row is None:
            raise UnknownImageRegistry(registry_id)
        url = registry_row.url
        username = registry_row.username
        password = registry_row.password
        creds = {"username": username, "password": password}

        return yarl.URL(url), creds

    @classmethod
    async def get_known_container_registries(
        cls,
        session: AsyncSession,
    ) -> Mapping[str, Mapping[str, yarl.URL]]:
        query_stmt = sa.select(ContainerRegistryRow).options(
            load_only(
                ContainerRegistryRow.project,
                ContainerRegistryRow.registry_name,
                ContainerRegistryRow.url,
            )
        )
        registries = cast(list[ContainerRegistryRow], (await session.scalars(query_stmt)).all())
        result: MutableMapping[str, MutableMapping[str, yarl.URL]] = {}
        for registry_row in registries:
            project = registry_row.project
            if project is None:
                continue
            registry_name = registry_row.registry_name
            url = registry_row.url
            if project not in result:
                result[project] = {}
            result[project][registry_name] = yarl.URL(url)
        return result

    @classmethod
    def from_dataclass(cls, data: ContainerRegistryData) -> Self:
        instance = cls(
            id=data.id,
            url=data.url,
            registry_name=data.registry_name,
            type=data.type,
            project=data.project,
            username=data.username,
            password=data.password,
            ssl_verify=data.ssl_verify,
            is_global=data.is_global,
            extra=data.extra,
        )
        instance.id = data.id
        return instance

    def to_dataclass(self) -> ContainerRegistryData:
        return ContainerRegistryData(
            id=self.id,
            url=self.url,
            registry_name=self.registry_name,
            type=self.type,
            project=self.project,
            username=self.username,
            password=self.password,
            ssl_verify=self.ssl_verify,
            is_global=self.is_global,
            extra=self.extra,
        )
