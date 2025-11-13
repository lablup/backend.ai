from typing import Type

from ..agent import AbstractAgent
from .agent import KubernetesAgent


def get_agent_cls() -> Type[AbstractAgent]:
    return KubernetesAgent
