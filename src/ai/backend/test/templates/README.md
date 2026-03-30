# templates

This package provides reusable templates for defining and composing test steps and flows. Templates encapsulate common patterns for resource creation, cleanup, and repeated flows, allowing for modular and maintainable test definitions.

Key components:
- `TestTemplate`: Abstract base class for all test templates, defining the interface for running test steps.
- `BasicTestTemplate`: Runs a single test code block.
- `WrapperTestTemplate`: Wraps another template, providing setup/teardown logic via async context managers.
- `SequenceTestTemplate`: Runs a sequence of templates in order.

Templates are used to build complex test scenarios by composing and reusing smaller, well-defined steps.
