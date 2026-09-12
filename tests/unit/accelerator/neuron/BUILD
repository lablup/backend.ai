python_test_utils(
    sources=[
        "*.py",
        "!test_*.py",
    ],
)

python_tests(
    name="tests",
    dependencies=[
        # The accelerator packages carry `tags=["accelerator"]`, which makes
        # `tools/pants-plugins/accelerator_wheels` strip their `src/ai/backend/*`
        # dependencies so each wheel can build standalone.  That stripping also
        # keeps `ai.backend.agent` out of a test sandbox that only depends on the
        # accelerator lib, so the plugin's own base classes must be named here.
        "src/ai/backend/agent/resources.py:src",
        "src/ai/backend/agent/docker/resources.py:../src",
    ],
)
