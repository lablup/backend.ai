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
        version="22.09.0.dev0",
    ),
    generate_setup=True,
)
