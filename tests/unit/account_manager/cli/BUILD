python_tests(
    dependencies=[
        # `account_manager/config.py` stats the sibling `server.py` at import; dependency inference
        # does not see it.
        "src/ai/backend/account_manager/server.py:src",
    ],
)
