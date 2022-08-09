python_sources(
    name="src",
    dependencies=[
        ":resources",
    ],
)

# This distribution is not actually uploaded to PyPI.
# We have separate krunner static distributions.
python_distribution(
    name="dist",
    dependencies=[
        ":src",
    ],
    provides=python_artifact(
        name="backend.ai-kernel-helper",
        description="Backend.AI Kernel Runner Prebuilt Binaries Package",
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
