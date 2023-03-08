python_sources(
    name="src",
    dependencies=[
        ":resources",
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
