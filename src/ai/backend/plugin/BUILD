python_sources(
    name="src",
    dependencies=[
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/**",
        "!//src/ai/backend/gateway/**",
        "!//src/ai/backend/manager/**",
        "!//src/ai/backend/agent/**",
        "!//src/ai/backend/storage/**",
        "!//src/ai/backend/wsproxy/**",
        "!//src/ai/backend/client/**",
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
