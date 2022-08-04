python_test_utils(
    name="test_utils",
    sources=[
        "conftest.py",
        "model_factory.py",
    ],
    dependencies=[
        ":fixtures",
    ],
)

python_tests(
    name="tests",
    dependencies=[
        "//:reqs#aiosqlite",  # not auto-inferred
        "//:reqs#psycopg2-binary",  # not auto-inferred
    ],
)

files(
    name="fixtures",
    sources=["fixtures/*"],
)
