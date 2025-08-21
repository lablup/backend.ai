python_sources()
python_requirements(
    name="reqs-pytest",
    source="pytest-requirements.txt",
    resolve="pytest",
    module_mapping={
        "pytest-mock": ["pytest_mock"],
        "pydantic": ["pydantic", "pydantic_core"],
    },
)
python_requirements(
    name="reqs-black",
    source="black-requirements.txt",
    resolve="black",
)
python_requirements(
    name="reqs-mypy",
    source="mypy-requirements.txt",
    resolve="mypy",
    module_mapping={
        "strawberry": ["strawberry_graphql"],
    },
)
python_requirements(
    name="reqs-coveragepy",
    source="coveragepy-requirements.txt",
    resolve="coverage-py",
)
python_requirements(
    name="reqs-towncrier",
    source="towncrier-requirements.txt",
    resolve="towncrier",
)
python_requirements(
    name="reqs-setuptools",
    source="setuptools-requirements.txt",
    resolve="setuptools",
)
