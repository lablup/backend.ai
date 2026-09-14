python_tests(
    dependencies=[
        # The kind catalog is a runtime scan of the entity package, which dependency
        # inference cannot see. Without this the sandbox holds only part of it.
        "src/ai/backend/common:src",
        # The generated fixture and the account fixtures it is rendered from.
        "fixtures/manager:json",
        "src/ai/backend/install:resources",
        # The revision is read by path: `versions/` is not a package, so nothing infers
        # it. The manager sources target carries every file under `src/`.
        "src/ai/backend/manager:src",
    ],
)
