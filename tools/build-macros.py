def visibility_private_component(**kwargs):
    """Private package not expected to be imported by anything else than itself."""
    allowed_dependencies = kwargs.get("allowed_dependencies", [])
    allowed_dependents = kwargs.get("allowed_dependents", [])

    __dependents_rules__(  # noqa: F821
        (
            {"type": "*"},  # applies to every target in the project
            "/**",  # code within this directory, recursively
            allowed_dependents,  # extra allowed dependents
            "//tests/**",  # tests can import the source files
            "//plugins/**",  # external plugins can import the source files
            "!*",  # no one else may import the source files
        )
    )
    __dependencies_rules__(  # noqa: F821
        (
            "*",  # applies to everything in this BUILD file
            "/**",  # may depend on anything in this subtree
            allowed_dependencies,  # extra allowed dependencies
            "//reqs#*",  # may depend on 3rd-party packages
            "//stubs/**",  # may depend on custom type stubs
            "!*",  # may not depend on anything else
        )
    )
