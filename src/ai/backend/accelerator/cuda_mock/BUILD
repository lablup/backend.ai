python_sources(
    name="lib",
    sources=["**/*.py"],
    dependencies=[
        ":resources",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":lib",
    ],
    provides=python_artifact(
        name="backend.ai-accelerator-cuda-mock",
        description="Backend.AI Accelerator Plugin for CUDA (Mockup)",
        license="Proprietary",
    ),
    entry_points={
        "backendai_accelerator_v20": {
            "cuda": "ai.backend.accelerator.cuda_mock.plugin:CUDAPlugin",
        }
    },
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
