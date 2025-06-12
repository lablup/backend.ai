from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.output.fields import image_fields
from ai.backend.client.session import AsyncSession
from ai.backend.common.types import ClusterMode
from ai.backend.test.templates.template import TestCode

# Test environment configuration
# TODO: Make these configurable loaderable by template wrapper
_IMAGE_NAME = "cr.backend.ai/stable/python:3.9-ubuntu20.04"
_IMAGE_ARCH = "x86_64"


class SessionCreationFailureLowResources(TestCode):
    def __init__(self) -> None:
        super().__init__()

    async def test(self) -> None:
        async with AsyncSession() as client_session:
            session_name = "test-session-creation-failure"

            result = await client_session.Image.get(
                _IMAGE_NAME, _IMAGE_ARCH, fields=[image_fields["labels"]]
            )
            labels = result["labels"]
            min_mem_label = next(
                filter(lambda label: label["key"] == "ai.backend.resource.min.mem", labels), None
            )

            if not min_mem_label:
                raise RuntimeError(
                    "Minimum memory label not found in image labels. Please check the image configuration."
                )

            min_mem = min_mem_label["value"]

            try:
                await client_session.ComputeSession.get_or_create(
                    _IMAGE_NAME,
                    name=session_name,
                    # This failed due to the need for additional space for shared memory.
                    resources={"cpu": 1, "mem": min_mem},
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                )
            except BackendAPIError as e:
                assert e.status == 400
                assert e.data["error_code"] == "api_generic_invalid-parameters"
