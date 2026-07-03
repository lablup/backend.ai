from __future__ import annotations

from ai.backend.common.config import ModelDefinitionDraft
from ai.backend.manager.api.gql.deployment.types.revision import (
    ModelConfigInputGQL,
    ModelDefinitionInputGQL,
    ModelHealthCheckInputGQL,
    ModelServiceConfigInputGQL,
)


class TestModelDefinitionInputGQL:
    def test_health_check_patch_preserves_baseline_service_fields(self) -> None:
        baseline = ModelDefinitionDraft.model_validate({
            "models": [
                {
                    "name": "Sehyo/Qwen3.5-35B-A3B-NVFP4",
                    "model_path": "/models",
                    "service": {
                        "pre_start_actions": [
                            {
                                "action": "run_command",
                                "args": {"command": ["chmod", "+x", "/models/start.sh"]},
                            }
                        ],
                        "start_command": ["/models/start.sh"],
                        "port": 8000,
                        "health_check": {
                            "enable": True,
                            "interval": 10.0,
                            "path": "/health",
                            "max_retries": 80,
                            "max_wait_time": 30.0,
                            "expected_status_code": 200,
                            "initial_delay": 300.0,
                        },
                    },
                }
            ]
        })
        gql_patch = ModelDefinitionInputGQL(
            models=[
                ModelConfigInputGQL(
                    service=ModelServiceConfigInputGQL(
                        health_check=ModelHealthCheckInputGQL(
                            enable=True,
                            interval=1.0,
                            path="1",
                            max_retries=1,
                            max_wait_time=1.0,
                            expected_status_code=101,
                            initial_delay=1.0,
                        )
                    )
                )
            ]
        )

        patch = gql_patch.to_pydantic().to_draft()
        assert patch.models is not None
        assert patch.models[0].service is not None
        assert "port" in patch.models[0].service.model_fields_set
        assert patch.models[0].service.port is None

        resolved = baseline.merge(patch).to_resolved()

        service = resolved.models[0].service
        assert service is not None
        assert service.port == 8000
        assert service.start_command == "/models/start.sh"
        assert service.health_check is not None
        assert service.health_check.path == "1"
        assert service.health_check.expected_status_code == 101
