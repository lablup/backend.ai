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
        "//src/ai/backend/client/**",
        "//src/ai/backend/storage/**",
        "//src/ai/backend/web/**",
        "//src/ai/backend/install/**",
        "//src/ai/backend/wsproxy/**",
        "//src/ai/backend/plugin/**",
    ],
    allowed_dependencies=[
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
        name="backend.ai-cli",
        description="Backend.AI Command Line Interface Helper",
        license="MIT",
    ),
    entry_points={
        "console_scripts": {
            "backend.ai": "ai.backend.cli.__main__:main",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

pex_binary(
    name="pex",
    dependencies=[
        ":src",
    ],
    entry_point="ai.backend.cli.__main__:main",
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
