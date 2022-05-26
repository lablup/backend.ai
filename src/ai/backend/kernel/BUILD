python_sources(
    name="lib",
    sources=[
        "**/*.py",
    ],
    dependencies=[
        ":resources",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":lib",
    ],
    provides=python_artifact(
        name="backend.ai-kernel",
        description="Backend.AI Kernel Runner",
        license="LGPLv3",
    ),
    generate_setup=True,
    repositories=[
        "@pypi",
    ],
)

resource(name="version", source="VERSION")

target(
    name="resources",
    dependencies=[
        ":version",
    ],
)
