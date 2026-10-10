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
        name="backend.ai-accelerator-neuron",
        description="Backend.AI Accelerator Plugin for AWS Neuron (Trainium/Inferentia) accelerators",
        license="LGPLv3",
    ),
    entry_points={
        "backendai_accelerator_v21": {
            "neuron": "ai.backend.accelerator.neuron.plugin:NeuronPlugin",
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
