python_sources(
    name="src",
    sources=["**/*.py"],
    dependencies=[
        ":resources",
        "stubs/trafaret:stubs",
        "//:reqs#pycares",  # aiodns runtime dependency - pin version explicitly
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/logging/**",
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
        name="backend.ai-common",
        description="Backend.AI commons library",
        license="LGPLv3",
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
