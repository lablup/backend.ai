python_sources(
    name="src",
    dependencies=[
        ":resources",
        "//:reqs#pytest",
        "//:reqs#pytest-dependency",
    ],
)

visibility_private_component(
    allowed_dependents=[],
    allowed_dependencies=[
        "//src/ai/backend/common/**",
        "//src/ai/backend/plugin/**",
        "//src/ai/backend/testutils/**",
    ],
)

pex_binary(
    name="cli",
    dependencies=[
        ":src",
    ],
    entry_point="ai.backend.test.cli.__main__:main",
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-test",
        description="Backend.AI Integration Test Suite",
        license="MIT",
    ),
    entry_points={
        "backendai_cli_v10": {
            "test": "ai.backend.test.cli.__main__:main",
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
