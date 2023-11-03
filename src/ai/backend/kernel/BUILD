python_sources(
    name="src",
    sources=[
        "**/*.py",  # per-lang sources are not auto-inferred
    ],
    dependencies=[
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/agent/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/runner/**",
        "//src/ai/backend/helpers/**",
        "//python-kernel.lock",
    ],
)

pex_binary(
    name="__main__",
    entry_point="__main__.py",
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
    ],
    provides=python_artifact(
        name="backend.ai-kernel",
        description="Backend.AI Kernel Runner",
        license="LGPLv3",
    ),
    generate_setup=True,
    tags=["wheel"],
)

resource(name="version", source="VERSION")

target(
    name="resources",
    dependencies=[
        ":version",
    ],
)

python_requirements(
    name="reqs",
    source="requirements.txt",
    resolve="python-kernel",
    module_mapping={
        "attrs": ["attr", "attrs"],
        "pyzmq": ["zmq"],
    },
)
