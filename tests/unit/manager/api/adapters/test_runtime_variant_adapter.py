from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from ai.backend.common.config import ModelDefinitionDraft
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.manager.api.adapters.runtime_variant.adapter import RuntimeVariantAdapter
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData


class TestRuntimeVariantDataToNode:
    def test_maps_start_command_to_command(self) -> None:
        data = RuntimeVariantData(
            id=RuntimeVariantID(uuid4()),
            name="vllm",
            description=None,
            reads_vfolder_config_files=False,
            default_model_definition=ModelDefinitionDraft.model_validate({
                "models": [
                    {
                        "service": {
                            "start_command": "vllm serve '{model_path}'",
                        },
                    }
                ]
            }),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=None,
        )

        node = RuntimeVariantAdapter._data_to_node(data)

        assert node.default_model_definition.models is not None
        service = node.default_model_definition.models[0].service
        assert service is not None
        assert service.command == "vllm serve '{model_path}'"
