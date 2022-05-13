from typing import Type

from ..agent import AbstractAgent
from .agent import DockerAgent


def get_agent_cls() -> Type[AbstractAgent]:
    return DockerAgent
