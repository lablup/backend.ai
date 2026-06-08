python_tests(
    # The rebellions accelerator distribution does not declare its agent/common
    # runtime imports as Pants dependencies, so pull the needed first-party
    # closure in explicitly for the test sandbox.
    dependencies=[
        "src/ai/backend/agent/stats.py:src",
        "src/ai/backend/agent/resources.py:src",
        "src/ai/backend/agent/types.py:src",
        "src/ai/backend/agent/docker/resources.py:../src",
        "src/ai/backend/common/config.py:src",
        "src/ai/backend/common/types.py:src",
        "src/ai/backend/common/logging.py:src",
    ],
)
