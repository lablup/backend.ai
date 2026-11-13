python_tests(
    overrides={
        "test_openapi.py": {
            "dependencies": [
                # `generate-openapi-spec` imports the API subapps by name; dependency inference
                # does not see it.
                "src/ai/backend/appproxy/coordinator:src",
                "src/ai/backend/appproxy/worker:src",
            ],
        },
    },
)
