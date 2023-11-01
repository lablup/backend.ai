python_sources(
    name="src",
    dependencies=[
        "src/ai/backend/cli:src",  # not auto-inferred
        "src/ai/backend/agent/docker:src",  # not auto-inferred
        "src/ai/backend/agent/kubernetes:src",  # not auto-inferred
        "src/ai/backend/runner:src",
        "src/ai/backend/helpers:src",
        "//:reqs#backend.ai-krunner-static-gnu",  # not auto-inferred
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/accelerator/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/accelerator/**",
        "//src/ai/backend/common/**",
        "//src/ai/backend/plugin/**",
        "//src/ai/backend/cli/**",  # not auto-inferred
        "//src/ai/backend/runner/**",
        "//src/ai/backend/kernel/**",
        "//src/ai/backend/helpers/**",
    ],
)

python_requirement(
    name="kernel-support",
    requirements=[],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "src/ai/backend/kernel:src",
        ":kernel-support",  # not auto-inferred
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-agent",
        description="Backend.AI Agent",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_cli_v10": {
            "ag": "ai.backend.agent.cli:main",
            "ag.start-server": "ai.backend.agent.server:main",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

pex_binary(
    name="pex",
    entry_point="ai.backend.cli.__main__",
    dependencies=[
        ":src",
        ":buildscript",
        "//src/ai/backend/accelerator/cuda_open:lib",
        "//src/ai/backend/accelerator/cuda_open:buildscript",
        "//src/ai/backend/accelerator/mock:lib",
        "//src/ai/backend/accelerator/mock:buildscript",
        "!!stubs/trafaret:stubs",
    ],
)
pex_binary(
    name="pex-watcher",
    entry_point="watcher.py",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
)

scie_binary(
    name="backendai-agent",
    dependencies=[":pex"],
)

scie_binary(
    name="backendai-agent-watcher",
    dependencies=[":pex-watcher"],
)

resource(name="version", source="VERSION")
resource(name="buildscript", source="BUILD")
resources(
    name="resources",
    dependencies=[
        ":version",
    ],
    sources=[
        "py.typed",
    ],
)
