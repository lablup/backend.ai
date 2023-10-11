python_test_utils(
    sources=["*.py"],
)

visibility_private_component(
    name="dep-rule",
    allowed_dependents=[
        "//src/ai/backend/test/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/common/**",
    ],
)
