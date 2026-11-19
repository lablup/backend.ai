from collections.abc import Callable

type Lint = Callable[[str, str], list[tuple[int, str]]]

DTO_RESPONSE = "src/ai/backend/common/dto/agent/response.py"


class TestDtoDataclassRule:
    def test_dataclass_in_common_dto_fails(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            @dataclass
            class PurgeImagesResp:
                responses: list[str]
        """
        assert lint(DTO_RESPONSE, source) == [(5, "BAI201")]

    def test_frozen_dataclass_in_common_dto_fails(self, lint: Lint) -> None:
        source = """
            import dataclasses

            @dataclasses.dataclass(frozen=True)
            class IngressRedisKey:
                prefix: str
        """
        assert lint("src/ai/backend/common/dto/appproxy/v2/ingress/types.py", source) == [
            (5, "BAI201")
        ]

    def test_pydantic_model_passes(self, lint: Lint) -> None:
        source = """
            from ai.backend.common.api_handlers import BaseResponseModel

            class PurgeImagesResp(BaseResponseModel):
                responses: list[str]
        """
        assert lint(DTO_RESPONSE, source) == []

    def test_dataclass_outside_common_dto_passes(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            @dataclass
            class Options:
                name: str
        """
        assert lint("src/ai/backend/common/types.py", source) == []
