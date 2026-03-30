from pydantic import BaseModel, ConfigDict, Field

from ai.backend.test.testcases.spec_manager import TestTag
from ai.backend.test.tester.dependency import TestContextInjectionModel


class BaseConfigModel(BaseModel):
    @staticmethod
    def snake_to_kebab_case(string: str) -> str:
        return string.replace("_", "-")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        use_enum_values=True,
        extra="allow",
        alias_generator=snake_to_kebab_case,
    )


class TestRunnerConfig(BaseConfigModel):
    concurrency: int = Field(
        default=10,
        description="The number of concurrent tests to run.",
        examples=[1, 2, 4],
    )
    exclude_tags: set[str] = Field(
        default_factory=set,
        description="Tags to exclude from the test run.",
        examples=[v.value for v in TestTag],
    )


class TesterConfig(BaseConfigModel):
    context: TestContextInjectionModel = Field(
        default_factory=TestContextInjectionModel,
        description="Configurations injected by the tester.",
    )
    runner: TestRunnerConfig = Field(
        default_factory=TestRunnerConfig,
        description="Configurations for the test runner.",
    )
