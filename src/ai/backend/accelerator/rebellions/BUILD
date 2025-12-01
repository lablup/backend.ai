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
        name="backend.ai-accelerator-rebellions",
        description="Backend.AI Accelerator Plugin for Rebellions NPUs",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_accelerator_v21": {
            "atom": "ai.backend.accelerator.rebellions.atom.plugin:ATOMPlugin",
            "atom_plus": "ai.backend.accelerator.rebellions.atom_plus.plugin:ATOMPlusPlugin",
            "atom_max": "ai.backend.accelerator.rebellions.atom_max.plugin:ATOMMaxPlugin",
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
