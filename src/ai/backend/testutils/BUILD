python_test_utils(
    sources=["*.py"],
)

visibility_private_component(
    allowed_dependents=[
        "//src/ai/backend/test/**",
    ],
    allowed_dependencies=[
        "//src/ai/backend/**",
        "!//src/ai/backend/web/**",
        "!//src/ai/backend/manager/**",
        "!//src/ai/backend/agent/**",
        "!//src/ai/backend/storage/**",
        "!//src/ai/backend/wsproxy/**",
    ],
)
