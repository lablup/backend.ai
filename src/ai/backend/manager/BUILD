python_sources(
    name="service",
    sources=["**/*.py"],
    dependencies=[
        "src/ai/backend/common:lib",
        ":resources",
    ],
)

pex_binary(
    name="server",
    dependencies=[
        ":service",
    ],
    entry_point="server.py",
)

python_distribution(
    name="dist",
    dependencies=[
        ":service",
    ],
    provides=python_artifact(
        name="backend.ai-manager",
        description="Backend.AI Manager",
        license="LGPLv3",
    ),
    generate_setup=True,
)

resources(
    name="resources",
    sources=[
        "**/py.typed",
    ],
)
