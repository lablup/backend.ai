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
    allowed_dependencies=[],
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
