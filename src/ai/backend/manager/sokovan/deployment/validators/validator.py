from abc import ABC

from ai.backend.manager.data.deployment.creator import DeploymentCreator


class DeploymentValidateRule(ABC):
    async def validate(self, spec: DeploymentCreator) -> None:
        raise NotImplementedError("Subclasses must implement this method")


class DeploymentValidator:
    _rules: list[DeploymentValidateRule]

    def __init__(self, rules: list[DeploymentValidateRule]) -> None:
        self._rules = rules

    async def validate(self, spec: DeploymentCreator) -> None:
        for rule in self._rules:
            await rule.validate(spec)
