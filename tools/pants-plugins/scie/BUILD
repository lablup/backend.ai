# Copyright 2023 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

python_sources()

python_distribution(
    name="scie-dist",
    dependencies=[":scie"],
    repositories=["@pypi"], # Configuration in ~/.pypirc
    wheel=True,
    sdist=False,
    provides=python_artifact(
        name="robotpajamas.pants.scie",
        version="0.0.2",
        description="A Pants plugin adding support for packaging SCIE.",
        license="Apache License, Version 2.0",
        project_urls={
            "Documentation": "https://github.com/sureshjoshi/pants-plugins",
            "Source": "https://github.com/sureshjoshi/pants-plugins",
            "Tracker": "https://github.com/sureshjoshi/pants-plugins/issues",
        },
        long_description_content_type="text/markdown",
        long_description=open("pants-plugins/experimental/scie/README.md").read(),
    ),
)
