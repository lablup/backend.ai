from collections.abc import Callable

type Lint = Callable[[str, str], list[tuple[int, str]]]

V2_TYPES = "src/ai/backend/common/dto/manager/v2/rbac/types.py"


class TestDtoConversionRule:
    def test_to_method_fails(self, lint: Lint) -> None:
        source = """
            class PermissionInput(BaseRequestModel):
                entity_type: str

                def to_permission(self) -> Permission:
                    return Permission(self.entity_type)
        """
        assert lint(V2_TYPES, source) == [(5, "BAI203")]

    def test_from_classmethod_fails(self, lint: Lint) -> None:
        source = """
            class RoleNode(BaseResponseModel):
                id: str

                @classmethod
                def from_data(cls, data: RoleData) -> "RoleNode":
                    return cls(id=data.id)
        """
        assert lint(V2_TYPES, source) == [(6, "BAI203")]

    def test_other_method_passes(self, lint: Lint) -> None:
        source = """
            class PermissionInput(BaseRequestModel):
                entity_type: str

                @field_validator("entity_type")
                @classmethod
                def topic_not_blank(cls, value: str) -> str:
                    return value.strip()
        """
        assert lint(V2_TYPES, source) == []

    def test_module_function_passes(self, lint: Lint) -> None:
        source = """
            def to_permission(value: str) -> Permission:
                return Permission(value)
        """
        assert lint(V2_TYPES, source) == []

    def test_conversion_method_outside_v2_passes(self, lint: Lint) -> None:
        source = """
            class ImageInfo(BaseResponseModel):
                def to_dict(self) -> dict[str, str]:
                    return {}
        """
        assert lint("src/ai/backend/common/dto/agent/response.py", source) == []
