python_sources(
    name="src",
    sources=["**/*.py"],
    dependencies=[
        ":resources",
        "stubs/trafaret:stubs",
        "//:reqs#pycares",  # aiodns runtime dependency - pin version explicitly
    ],
)

# Dependency direction within common: dto may depend on schema, not the reverse.
# Paths starting with "/" are relative to this (common) directory.
__dependencies_rules__(
    # schema: must not depend on dto.
    (
        "/schema/**",
        "!/dto/**",
        "/**",
        "//src/ai/backend/logging/**",
        "//src/ai/backend/plugin/**",
        "//reqs#*",
        "//stubs/**",
        "!*",
    ),
    # default: every other file in the component.
    (
        "*",
        "/**",
        "//src/ai/backend/logging/**",
        "//src/ai/backend/plugin/**",
        "//reqs#*",
        "//stubs/**",
        "!*",
    ),
)

# Who may import the common component (equivalent to visibility_private_component).
__dependents_rules__(
    (
        {"type": "*"},
        "/**",  # code within this component may import itself
        "//src/ai/backend/**",  # allowed extra dependents (all backend components)
        "//tests/**",  # tests may import the source files
        "//plugins/**",  # external plugins may import the source files
        "!*",  # no one else may import the source files
    )
)

python_distribution(
    name="dist",
    dependencies=[
        ":src",
        "!!stubs/trafaret:stubs",
    ],
    provides=python_artifact(
        name="backend.ai-common",
        description="Backend.AI commons library",
        license="LGPLv3",
    ),
    generate_setup=True,
    tags=["wheel"],
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
