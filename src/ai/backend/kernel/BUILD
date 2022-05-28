python_sources(
    name="lib",
    sources=[
        "**/*.py",
    ],
    interpreter_constraints=[">=3.8"],
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
