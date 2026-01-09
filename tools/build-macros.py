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


def common_scie_config(build_style, *, entry_point="ai.backend.cli.__main__"):
    build_style_to_tag = {
        "lazy": "lazy",
        "eager": "fat",
    }
    return {
        "extra_build_args": [
            f"--scie={build_style}",
            "--scie-python-version=3.13.7",
            "--scie-pbs-release=20250818",
            "--scie-pbs-stripped",
            # WARNING: PEX 2.18 or later offers `--scie-name-style` and `--scie-only` option, but we
            # should NOT use them because Pants expects the PEX subprocess to generate the output file
            # as it configured in the `output_path` field while removing files having other names.
        ],
        "entry_point": entry_point,
        "tags": ["scie", build_style_to_tag[build_style]],
        "output_path": "${target_name_normalized}",
    }
