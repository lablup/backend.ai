python_sources(
    name="service",
    sources=["**/*.py"],
    dependencies=[
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
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-storage-proxy",
        description="Backend.AI Storage Proxy",
        license="LGPLv3",
    ),
    entry_points={},
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
