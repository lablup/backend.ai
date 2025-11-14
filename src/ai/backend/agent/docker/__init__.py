from typing import Type

from ..agent import AbstractAgent
from ..resources import AbstractResourceDiscovery
from .agent import DockerAgent
from .resources import DockerResourceDiscovery


def get_agent_cls() -> Type[AbstractAgent]:
    return DockerAgent


def get_resource_discovery_cls() -> Type[AbstractResourceDiscovery]:
    return DockerResourceDiscovery
