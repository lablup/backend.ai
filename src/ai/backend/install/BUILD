python_sources(
    name="src",
    dependencies=[
        ":resources",
        "./configs:src",
        "./fixtures:src",
    ],
)

visibility_private_component(
    allowed_dependents=[],
    allowed_dependencies=[
        "//src/ai/backend/cli/**",
        "//src/ai/backend/common/**",
        "//src/ai/backend/plugin/**",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-install",
        description="Backend.AI Installer",
        license="MIT",
    ),
    entry_points={
        "backendai_cli_v10": {
            "install": "ai.backend.install.cli:main",
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
        "!!stubs/trafaret:stubs",
    ],
)

scie_binary(
    name="backendai-install",
    fat=False,
    dependencies=[":pex"],
    tags=["scie", "lazy"],
)

scie_binary(
    name="backendai-install-fat",
    fat=True,
    dependencies=[":pex"],
    tags=["scie", "fat"],
)

run_shell_command(
    name="checksum",
    command=(
        "find . -name 'backendai-install-*' -not -name '*.sha256' | xargs -I {} sh -c 'sha256sum"
        " {} > {}.sha256'"
    ),
    workdir="/dist",
    execution_dependencies=[
        ":backendai-install",
        ":backendai-install-fat",
    ],
    tags=["checksum"],
)

resource(name="version", source="VERSION")
resource(name="buildscript", source="BUILD")
resources(
    name="resources",
    dependencies=[
        ":version",
        "./configs:templates",
        "./fixtures:resources",
    ],
    sources=[
        "**/py.typed",
        "app.tcss",
    ],
)
