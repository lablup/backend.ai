def visibility_private_component(**kwargs):
    """Private package not expected to be imported by anything else than itself."""
    name = kwargs["name"]
    allowed_dependencies = kwargs.get("allowed_dependencies", [])
    allowed_dependents = kwargs.get("allowed_dependents", [])

    __dependents_rules__(
        (
            {"type": "*"}, # applies to every target in the project
            "/**",  # code within this directory, recursively
            allowed_dependents,  # extra allowed dependents
            "//tests/**",  # tests can import the source files
            "//plugins/**",  # external plugins can import the source files
            "!*",  # no one else may import the source files
        )
    )
    __dependencies_rules__(
        (
            "*",  # applies to everything in this BUILD file
            "/**",  # may depend on anything in this subtree
            "//:reqs",  # may depend on 3rd-party packages
            allowed_dependencies,  # extra allowed dependencies
            "!*",  # may not depend on anything else
        )
    )


python_requirements(
    name="reqs",
    source="requirements.txt",
    module_mapping={
        "aiodataloader-ng": ["aiodataloader"],
        "aiomonitor-ng": ["aiomonitor"],
        "attrs": ["attr", "attrs"],
        "aiohttp-session": ["aiohttp_session"],
        "pycryptodome": ["Crypto"],
        "python-dateutil": ["dateutil", "dateutil.parser", "dateutil.tz"],
        "python-json-logger": ["pythonjsonlogger"],
        "pyzmq": ["zmq"],
        "PyYAML": ["yaml"],
        "typing-extensions": ["typing_extensions"],
        "more-itertools": ["more_itertools"],
        "zipstream-new": ["zipstream"],
    },
    type_stubs_module_mapping={
        "types-aiofiles": ["aiofiles"],
        "types-cachetools": ["cachetools"],
        "types-Jinja2": ["jinja2"],
        "types-PyYAML": ["yaml"],
        "types-python-dateutil": ["dateutil", "dateutil.parser", "dateutil.tz"],
        "types-redis": ["redis"],
        "types-setuptools": [
            "setuptools",
            "pkg_resources",
            "pytest",
            "ai.backend.testutils",
            "ai.backend.test",
            "tests",
        ],
        "types-six": ["six", "graphql", "promise", "ai.backend.manager.models"],
        "types-tabulate": ["tabulate"],
    },
)
