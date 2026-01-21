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
        name="backend.ai-accelerator-tenstorrent",
        description="Backend.AI Accelerator Plugin for Tenstorrent accelerators",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_accelerator_v21": {
            "tt-n300": "ai.backend.accelerator.tenstorrent.n300.plugin:TTn300Plugin",
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
