python_sources(
    name="src",
    sources=["**/*.py"],
    dependencies=[
        ":resources",
        "src/ai/backend/runner:src",  # libbaihook builds, read with importlib.resources
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/manager/**",
        "//src/ai/backend/testutils/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/agent/**",  # the kernel runner client (AbstractCodeRunner)
        "//src/ai/backend/common/**",
        "//src/ai/backend/logging/**",
        "//src/ai/backend/runner/**",
        "//src/ai/backend/sokovan_core/**",
    ],
)

resource(name="version", source="VERSION")
resources(
    name="resources",
    dependencies=[
        ":version",
    ],
    sources=[
        "**/py.typed",
    ],
)
