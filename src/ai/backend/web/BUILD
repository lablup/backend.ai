python_sources(
    name="src",
    dependencies=[
        ":resources",
        "//:reqs#coloredlogs",  # indirectly referred by logging config string
    ],
)

visibility_private_component(
    allowed_dependents=[],
    allowed_dependencies=[
        "//src/ai/backend/common/**",
        "//src/ai/backend/plugin/**",
        "//src/ai/backend/client/**",
        "//src/ai/backend/cli/**",
    ],
)

pex_binary(
    name="server",
    dependencies=[
        ":src",
    ],
    entry_point="server.py",
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
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
