from __future__ import annotations

import re
from pathlib import Path

from pants.backend.python.goals.setup_py import SetupKwargs, SetupKwargsRequest
from pants.engine.fs import DigestContents, GlobMatchErrorBehavior, PathGlobs
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.target import Target
from pants.engine.unions import UnionRule


class CustomSetupKwargsRequest(SetupKwargsRequest):
    @classmethod
    def is_applicable(cls, _: Target) -> bool:
        # We always use our custom `setup()` kwargs generator for `python_distribution` targets in
        # this repo.
        return True


license_classifier_map = {
    "LGPLv3": "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
    "Apache 2.0": "License :: OSI Approved :: Apache Software License",
    "BSD": "License :: OSI Approved :: BSD License",
    "MIT": "License :: OSI Approved :: MIT License",
}


@rule
async def setup_kwargs_plugin(request: CustomSetupKwargsRequest) -> SetupKwargs:
    kwargs = request.explicit_kwargs.copy()

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

    # Validate that required fields are set.
    if not kwargs["name"].startswith("backend.ai-"):
        raise ValueError(
            f"Invalid `name` kwarg in the `provides` field for {request.target.address}. The name "
            f"must start with 'backend.ai-', but was {kwargs['name']}.",
        )
    if "description" not in kwargs:
        raise ValueError(
            f"Missing a `description` kwarg in the `provides` field for {request.target.address}.",
        )

    # Add classifiers. We preserve any that were already set.
    standard_classifiers = [
        "Intended Audience :: Developers",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Environment :: No Input/Output (Daemon)",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development",
    ]
    if re.search(r"\.?dev\d*$", VERSION):
        standard_classifiers.append("Development Status :: 2 - Pre-Alpha")
    elif re.search(r"\.?a(lpha)?\d*$", VERSION):
        standard_classifiers.append("Development Status :: 3 - Alpha")
    elif re.search(r"\.?b(eta)?\d*$", VERSION):
        standard_classifiers.append("Development Status :: 4 - Beta")
    elif re.search(r"\.?rc?\d*$", VERSION):
        standard_classifiers.append("Development Status :: 4 - Beta")
    else:
        standard_classifiers.append("Development Status :: 5 - Production/Stable")

    license_classifier = license_classifier_map.get(kwargs["license"])
    if license_classifier:
        standard_classifiers.append(license_classifier)

    kwargs["classifiers"] = [*standard_classifiers, *kwargs.get("classifiers", [])]

    # Determine the long description by reading from ABOUT.md and the release notes.
    spec_path = Path(request.target.address.spec_path)
    if (spec_path / "README.md").is_file():
        readme_path = spec_path / "README.md"
    elif (spec_path / "README.rst").is_file():
        readme_path = spec_path / "README.rst"
    else:
        readme_path = spec_path / "README"
    _digest_contents = await Get(
        DigestContents,
        PathGlobs(
            [str(readme_path)],
            description_of_origin="setupgen plugin",
            glob_match_error_behavior=GlobMatchErrorBehavior.error,
        ),
    )
    long_description = _digest_contents[0].content.decode()

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
        author="Lablup Inc. and contributors",
        zip_safe=False,
    )
    conflicting_hardcoded_kwargs = set(kwargs.keys()).intersection(hardcoded_kwargs.keys())
    if conflicting_hardcoded_kwargs:
        raise ValueError(
            f"These kwargs should not be set in the `provides` field for {request.target.address} "
            "because Pants's internal plugin will automatically set them: "
            f"{sorted(conflicting_hardcoded_kwargs)}",
        )
    kwargs.update(hardcoded_kwargs)

    return SetupKwargs(kwargs, address=request.target.address)


def rules():
    return [
        *collect_rules(),
        UnionRule(SetupKwargsRequest, CustomSetupKwargsRequest),
    ]
