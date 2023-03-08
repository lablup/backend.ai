python_sources(
    name="src",
    dependencies=[
        ":resources",
        "stubs/trafaret:stubs",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "src/ai/backend/common/plugin:src",
        "src/ai/backend/common/web/session:src",  # not auto-inferred
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-common",
        description="Backend.AI commons library",
        license="LGPLv3",
    ),
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
