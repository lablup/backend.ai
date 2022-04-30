python_sources(
    name="lib",
    sources=["**/*.py"],
    dependencies=[
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":lib",
    ],
    provides=python_artifact(
        name="backend.ai-common",
        description="Backend.AI commons library",
        license="LGPLv3",
    ),
    generate_setup=True,
)
