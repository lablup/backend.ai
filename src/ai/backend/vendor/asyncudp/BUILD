python_sources(
    name="src",
    dependencies=[
        ":version",
    ],
    # Since this is a vendored libary, we don't force our linters/checkers.
    skip_black=True,
    skip_flake8=True,
    skip_isort=True,
    skip_mypy=True,
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-vendor-asyncudp",
        description="asyncudp",
        license="MIT",
    ),
    entry_points={},
    generate_setup=True,
    tags=["wheel"],
)

resource(name="version", source="VERSION")
