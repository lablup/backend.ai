from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.output.fields import image_fields
from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.templates.template import TestCode
from ai.backend.test.utils.exceptions import UnexpectedSuccess


class SessionCreationFailureLowResources(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        image_dep = ImageContext.current()
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        session_name = f"test_failure_{str(test_id)}"

        result = await client_session.Image.get(
            image_dep.name, image_dep.architecture, fields=[image_fields["labels"]]
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
                image_dep.name,
                architecture=image_dep.architecture,
                name=session_name,
                # This failed due to the need for additional space for shared memory.
                resources={"cpu": 1, "mem": min_mem},
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
            )
            raise UnexpectedSuccess("Expected BackendAPIError for low resources was not raised")
        except BackendAPIError as e:
            assert e.status == 400
            assert e.data["error_code"] == "api_generic_invalid-parameters"
