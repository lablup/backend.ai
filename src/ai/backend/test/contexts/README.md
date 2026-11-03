# contexts

This package defines context classes that pass values and state between test steps in the testing framework. A context shares values such as session objects, ids and other resources that test execution creates or changes, so a later step can read the result of an earlier step.

Typical usage wraps a resource such as a client session or a test id and gives test scenarios a consistent interface to the shared state.

Example classes:
- `TestSpecMetaContext`: Stores test metadata, such as `test_id`.
- `ClientSessionContext`: Stores and provides an asynchronous client session.

These context classes are typically used as part of the setup and teardown process of a test scenario.
