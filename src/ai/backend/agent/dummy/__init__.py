from typing import Type

from ..agent import AbstractAgent
from .agent import DummyAgent


def get_agent_cls() -> Type[AbstractAgent]:
    return DummyAgent
