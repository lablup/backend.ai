python_sources(
    name="src",
    dependencies=[
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/manager/**",
        "//src/ai/backend/agent/**",
        "//src/ai/backend/storage/**",
        "//src/ai/backend/web/**",
        "//src/ai/backend/client/**",
        "//src/ai/backend/common/**",
        "//src/ai/backend/cli/**",
        "//src/ai/backend/test/**",
        "//src/ai/backend/testutils/**",
        "//src/ai/backend/install/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/cli/**",
        "//src/ai/backend/common/**",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-plugin",
        description="Backend.AI Plugin Subsystem",
        license="MIT",
    ),
    entry_points={
        "backendai_cli_v10": {
            "plugin": "ai.backend.plugin.cli:main",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

resource(name="version", source="VERSION")

resources(
    name="resources",
    dependencies=[
        ":version",
    ],
    sources=[
        "**/py.typed",
    ],
)

pex_binary(
    name="pex",
    entry_point="ai.backend.cli.__main__",
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

scie_binary(
    name="backendai-plugin",
    fat=False,
    dependencies=[":pex"],
    tags=["scie", "lazy"],
)

scie_binary(
    name="backendai-plugin-fat",
    fat=True,
    dependencies=[":pex"],
    tags=["scie", "fat"],
)

resource(name="buildscript", source="BUILD")
