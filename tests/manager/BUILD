python_test_utils(
    name="test_utils",
    sources=[
        "conftest.py",
        "model_factory.py",
    ],
    dependencies=[
        ":fixtures",
        "src/ai/backend/manager/api:src",  # indirectly referred via create_app_and_client() fixture
        "//:reqs#psycopg2-binary",  # not auto-inferred
        "//:reqs#aiosqlite",  # not auto-inferred
    ],
)

python_tests(name="tests")

files(
    name="fixtures",
    sources=["fixtures/*"],
)
