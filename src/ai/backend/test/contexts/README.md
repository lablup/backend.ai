# contexts

This package defines context classes used to pass values and state between different test steps in the testing framework. Contexts are used to share information such as session objects, IDs, or other resources that are created or modified during test execution, making it possible for later steps to access results from previous steps.

Typical usage includes wrapping resources like client sessions or test IDs, and providing a consistent interface for test scenarios to access shared state.

Example classes:
- `TestSpecMetaContext`: Store test metadata like test_id.
- `ClientSessionContext`: Stores and provides an asynchronous client session.

These context classes are typically used as part of the test scenario setup and teardown process.
