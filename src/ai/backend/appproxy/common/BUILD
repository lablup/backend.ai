python_sources(
    name="src",
    sources=["**/*.py"],
    dependencies=[
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/appproxy/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/common/**",
        "//src/ai/backend/logging/**",
    ],
)

resources(
    name="resources",
    dependencies=[
        ":version",
    ],
    sources=[
        "**/py.typed",
        "templates/*",
    ],
)

resource(name="version", source="VERSION")

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-appproxy-common",
        description="Backend.AI AppProxy Common",
        license="Proprietary",
    ),
    generate_setup=True,
    tags=["wheel"],
)
