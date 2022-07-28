python_sources(
    name="service",
    sources=["**/*.py"],
    dependencies=[
        "src/ai/backend/client:lib",
        ":resources",
        "//:reqs#coloredlogs",  # indirectly referred by logging config string
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
        name="backend.ai-webserver",
        description="Backend.AI WebUI Host",
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
        "static/**/*",
        "templates/**/*",
    ],
)
