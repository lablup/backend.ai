python_sources(
    name="lib",
    interpreter_constraints=[">=3.8"],
    dependencies=[
        ":resources",
    ],
)

# This distribution is not actually uploaded to PyPI.
# We have separate krunner static distributions.
python_distribution(
    name="dist",
    dependencies=[
        ":lib",
    ],
    provides=python_artifact(
        name="backend.ai-kernel-helper",
        description="Backend.AI Kernel Runner Prebuilt Binaries Package",
        license="LGPLv3",
    ),
    generate_setup=True,
    repositories=[
        "@pypi",
    ],
)

resource(name="version", source="VERSION")

target(
    name="resources",
    dependencies=[
        ":version",
    ],
)
