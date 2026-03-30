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
        name="backend.ai-accelerator-rocm",
        description="Backend.AI Accelerator Plugin for AMD GPUs",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_accelerator_v21": {
            "rocm": "ai.backend.accelerator.rocm.plugin:ROCmPlugin",
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
