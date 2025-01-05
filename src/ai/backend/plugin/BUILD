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
        "!//src/ai/backend/web/**",
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
    name="backendai-plugin",
    extra_build_args=["--scie", "lazy"],
    tags=["scie", "lazy"],
    entry_point="ai.backend.cli.__main__",
    output_path="${target_name_normalized}",
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

pex_binary(
    name="backendai-plugin-fat",
    extra_build_args=["--scie", "eager"],
    tags=["scie", "fat"],
    entry_point="ai.backend.cli.__main__",
    output_path="${target_name_normalized}",
    dependencies=[
        ":src",
        ":buildscript",
        "!!stubs/trafaret:stubs",
    ],
)

resource(name="buildscript", source="BUILD")
