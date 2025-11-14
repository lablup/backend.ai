from typing import Type

from ..agent import AbstractAgent
from ..resources import AbstractResourceDiscovery
from .agent import KubernetesAgent
from .resources import KubernetesResourceDiscovery


def get_agent_cls() -> Type[AbstractAgent]:
    return KubernetesAgent


def get_resource_discovery_cls() -> Type[AbstractResourceDiscovery]:
    return KubernetesResourceDiscovery
