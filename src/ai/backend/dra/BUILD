python_sources(
    name="src",
    sources=["**/*.py"],
    dependencies=[
        ":resources",
    ],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/kube/**",
        "//src/ai/backend/testutils/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/agent/**",  # the accelerator plugin base classes
        "//src/ai/backend/common/**",
        "//src/ai/backend/logging/**",
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
