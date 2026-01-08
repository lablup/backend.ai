python_sources(
    name="lib",
    sources=["**/*.py"],
    dependencies=[
        ":resources",
    ],
    tags=["accelerator"],
)

python_distribution(
    name="dist",
    dependencies=[
        ":lib",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-accelerator-graphcore-ipu",
        description="Backend.AI Accelerator Plugin for Graphcore IPUs",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_accelerator_v21": {
            "ipu": "ai.backend.accelerator.ipu.plugin:IPUPlugin",
        }
    },
    generate_setup=True,
    tags=["wheel"],
)

resource(name="version", source="VERSION")
resource(name="buildscript", source="BUILD")
resources(
    name="resources",
    dependencies=[
        ":version",
    ],
    sources=[
        "**/py.typed",
    ],
)
