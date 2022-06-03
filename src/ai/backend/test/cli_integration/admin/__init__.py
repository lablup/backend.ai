"""
An integration test for the Backend.AI admin APIs.

It runs and checks the result of a series of CRUD commands for various entities including domain, group,
user, scaling group, resource policy, resource preset, etc.

The location of the client executable and the credential scripts are configured as environment variables
read by the pytest fixtures in the ai.backend.test.cli_integration.conftest module.
"""
