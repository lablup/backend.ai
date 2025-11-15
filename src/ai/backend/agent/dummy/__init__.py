from typing import Type

from ..agent import AbstractAgent
from ..resources import AbstractResourceDiscovery
from .agent import DummyAgent
from .resources import DummyResourceDiscovery


def get_agent_cls() -> Type[AbstractAgent]:
    return DummyAgent


def get_resource_discovery() -> AbstractResourceDiscovery:
    return DummyResourceDiscovery()
