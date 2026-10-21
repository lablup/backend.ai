from ai.backend.common.config import (
    ModelServiceConfig,
    ServiceInterpolation,
    ServiceInterpolationDelimiter,
    ServiceInterpolationMode,
)
from ai.backend.kernel.service import ServiceDefinition, ServiceParser


class TestModelServiceConfigContract:
    async def test_kernel_reads_interpolation_dumped_from_model_service_config(self) -> None:
        config = ModelServiceConfig(
            start_command="serve",
            port=8000,
            interpolation=ServiceInterpolation(
                mode=ServiceInterpolationMode.DELIMITER,
                delimiter=ServiceInterpolationDelimiter(start="{{", end="}}"),
            ),
        )
        service_parser = ServiceParser({"x": "1"})
        service_parser.services["app"] = ServiceDefinition(command=["{{ x }} {x}"])

        cmdargs, _ = await service_parser.start_service(
            "app", set(), {"interpolation": config.model_dump(mode="json")["interpolation"]}
        )

        assert cmdargs == ["1 {x}"]
