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
        name="backend.ai-accelerator-habana",
        description="Backend.AI Accelerator Plugin for Intel® Gaudi® HPUs",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_accelerator_v21": {
            "gaudi2": "ai.backend.accelerator.habana.gaudi2.plugin:Gaudi2Plugin",
            "gaudi3": "ai.backend.accelerator.habana.gaudi3.plugin:Gaudi3Plugin",
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

shell_sources()
