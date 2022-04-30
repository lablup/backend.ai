from __future__ import annotations

from pants.backend.python.goals.setup_py import SetupKwargs, SetupKwargsRequest
from pants.engine.fs import DigestContents, GlobMatchErrorBehavior, PathGlobs
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.unions import UnionRule



class CustomSetupKwargsRequest(SetupKwargsRequest):
    @classmethod
    def is_applicable(cls, _: Target) -> bool:
        # We always use our custom `setup()` kwargs generator for `python_distribution` targets in
        # this repo.
        return True


@rule
async def setup_kwargs_plugin(request: CustomSetupKwargsRequest) -> SetupKwargs:
    kwargs = request.explicit_kwargs.copy()

    # Validate that required fields are set.
    if not kwargs["name"].startswith("backend.ai-"):
        raise ValueError(
            f"Invalid `name` kwarg in the `provides` field for {request.target.address}. The name "
            f"must start with 'backend.ai-', but was {kwargs['name']}."
        )
    if "description" not in kwargs:
        raise ValueError(
            f"Missing a `description` kwarg in the `provides` field for {request.target.address}."
        )

    # Add classifiers. We preserve any that were already set.
    standard_classifiers = [
        "Intended Audience :: Developers",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
    ]
    kwargs["classifiers"] = [*standard_classifiers, *kwargs.get("classifiers", [])]

    # Determine the long description by reading from ABOUT.md and the release notes.
    _digest_contents = await Get(
        DigestContents,
        PathGlobs(
            [f"packages/{kwargs['name']}/README.md"],
            description_of_origin="setupgen plugin",
            glob_match_error_behavior=GlobMatchErrorBehavior.error,
        ),
    )
    long_description = _digest_contents[0].content.decode()

    # Single-source the version from VERSION.
    _digest_contents = await Get(
        DigestContents,
        PathGlobs(
            ["VERSION"],
            description_of_origin="setupgen plugin",
            glob_match_error_behavior=GlobMatchErrorBehavior.error,
        ),
    )
    VERSION = _digest_contents[0].content.decode()

    # Hardcode certain kwargs and validate that they weren't already set.
    hardcoded_kwargs = dict(
        version=VERSION,
        long_description=long_description,
        long_description_content_type="text/markdown",
        url="https://github.com/lablup/backend.ai",
        project_urls={
            "Documentation": "https://docs.backend.ai/",
            "Source": "https://github.com/lablup/backend.ai",
        },
        zip_safe=False,
    )
    conflicting_hardcoded_kwargs = set(kwargs.keys()).intersection(hardcoded_kwargs.keys())
    if conflicting_hardcoded_kwargs:
        raise ValueError(
            f"These kwargs should not be set in the `provides` field for {request.target.address} "
            "because Pants's internal plugin will automatically set them: "
            f"{sorted(conflicting_hardcoded_kwargs)}"
        )
    kwargs.update(hardcoded_kwargs)

    return SetupKwargs(kwargs, address=request.target.address)


def rules():
    return [
        *collect_rules(),
        UnionRule(SetupKwargsRequest, CustomSetupKwargsRequest),
    ]
