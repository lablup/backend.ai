python_sources(
    name="src",
    dependencies=[
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[
    ],
    allowed_dependencies=[
        "//src/ai/backend/common/**",
        "//src/ai/backend/plugin/**",
        "//src/ai/backend/cli/**",  # not auto-inferred
    ],
)

pex_binary(
    name="server",
    dependencies=[
        ":src",
    ],
    entry_point="server.py",
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-watcher",
        description="Backend.AI Watcher",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_cli_v10": {
            "watcher": "ai.backend.watcher.cli:main",
            "watcher.start-server": "ai.backend.watcher.server:main",
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
        "!!stubs/trafaret:stubs",
    ],
)

scie_binary(
    name="backendai-watcher",
    dependencies=[":pex"],
)

resource(name="version", source="VERSION")
resource(name="buildscript", source="BUILD")
resources(
    name="resources",
    dependencies=[
        ":version",
    ],
    sources=[
        "**/py.typed",
    ],
)
