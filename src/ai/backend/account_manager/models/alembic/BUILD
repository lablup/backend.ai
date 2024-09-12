python_sources(
    name="migrations",
    dependencies=[
        ":resources",
        ":src",
    ],
)

python_sources(
    name="src",
    sources=["versions/*.py"],
)

resources(
    name="resources",
    sources=[
        "script.py.mako",
        "revision_history/*.json",
    ],
)
