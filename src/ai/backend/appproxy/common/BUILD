resource(name="version", source="VERSION")

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
    ],
    provides=python_artifact(
        name="backend.ai-appproxy-common",
        description="Backend.AI AppProxy Common",
        license="Proprietary",
    ),
    generate_setup=True,
    tags=["wheel"],
)
