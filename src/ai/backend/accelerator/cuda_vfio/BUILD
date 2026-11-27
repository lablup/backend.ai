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
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-accelerator-cuda-vfio",
        description="Backend.AI Accelerator Plugin for CUDA GPUs bound to vfio-pci",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_accelerator_v21": {
            "cuda_vfio": "ai.backend.accelerator.cuda_vfio.plugin:CUDAVFIOPlugin",
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
