"""Image-related data types."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.types import AutoPullBehavior, ImageConfig


@dataclass(frozen=True)
class ImageIdentifier:
    """Identifier for an image with architecture."""

    image: str
    architecture: str


@dataclass
class ImageConfigData:
    """Image configuration data resolved from database."""

    canonical: str
    architecture: str
    project: str | None
    is_local: bool
    digest: str
    labels: dict[str, str]
    registry_name: str
    registry_url: str
    registry_username: str | None
    registry_password: str | None

    def to_image_config(self, auto_pull: AutoPullBehavior) -> ImageConfig:
        """
        Convert ImageConfigData to ImageConfig format for agents.

        :param auto_pull: Auto pull behavior setting
        :return: ImageConfig dictionary for agent RPC calls
        """
        return ImageConfig(
            architecture=self.architecture,
            project=self.project,
            canonical=self.canonical,
            is_local=self.is_local,
            digest=self.digest,
            labels=self.labels,
            repo_digest=None,
            registry={
                "name": self.registry_name,
                "url": self.registry_url,
                "username": self.registry_username,
                "password": self.registry_password,
            },
            auto_pull=auto_pull,
        )
