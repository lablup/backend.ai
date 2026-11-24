from collections.abc import Callable

type Lint = Callable[[str, str], list[tuple[int, str]]]

V2_RESPONSE = "src/ai/backend/common/dto/manager/v2/user/response.py"


class TestDtoSchemaBaseRule:
    def test_backend_ai_schema_base_fails(self, lint: Lint) -> None:
        source = """
            from ai.backend.common.types import BackendAISchema

            class UserBasicInfo(BackendAISchema):
                username: str
        """
        assert lint(V2_RESPONSE, source) == [(4, "BAI202")]

    def test_backend_ai_schema_attribute_base_fails(self, lint: Lint) -> None:
        source = """
            from ai.backend.common import types

            class SliderOption(types.BackendAISchema):
                min: float
        """
        filename = "src/ai/backend/common/dto/manager/v2/runtime_variant_preset/types.py"
        assert lint(filename, source) == [(4, "BAI202")]

    def test_response_model_base_passes(self, lint: Lint) -> None:
        source = """
            from ai.backend.common.api_handlers import BaseResponseModel

            class UserBasicInfo(BaseResponseModel):
                username: str
        """
        assert lint(V2_RESPONSE, source) == []

    def test_backend_ai_schema_outside_v2_passes(self, lint: Lint) -> None:
        source = """
            from ai.backend.common.types import BackendAISchema

            class UserInfo(BackendAISchema):
                username: str
        """
        assert lint("src/ai/backend/common/dto/manager/user/response.py", source) == []
