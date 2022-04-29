resource(name="pyproject", source="pyproject.toml")

python_sources(
    name="lib",
    sources=["**/*.py"],
    dependencies=[
        ":pyproject",
        "//:reqs",
    ],
)

python_distribution(
    name="dist",
    dependencies=[
        ":lib",
        ":pyproject",
    ],
    provides=python_artifact(
        name="backend.ai-common",
        version="22.09.0.dev0",
    ),
    generate_setup=False,
    # wheel_config_settings={"--global-option": ["--universal", "false"]},
)
