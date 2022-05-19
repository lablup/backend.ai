python_sources(
    name="lib",
    sources=["**/*.py"],
    dependencies=[
        ":resources",
        "stubs/trafaret:stubs",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":lib",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-common",
        description="Backend.AI commons library",
        license="LGPLv3",
    ),
    generate_setup=True,
    repositories=[
        "@pypi",
    ],
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
