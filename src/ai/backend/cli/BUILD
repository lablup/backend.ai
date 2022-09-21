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
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-cli",
        description="Backend.AI Command Line Interface Helper",
        license="MIT",
    ),
    entry_points={
        "console_scripts": {
            "backend.ai": "ai.backend.cli.__main__:main",
        },
    },
    generate_setup=True,
    tags=["wheel"],
)

pex_binary(
    name="cli",
    dependencies=[
        ":src",
    ],
    entry_point="ai.backend.cli.__main__:main",
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
