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
        name="backend.ai-storage-proxy",
        description="Backend.AI Storage Proxy",
        license="LGPLv3",
    ),
    entry_points={
    },
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
