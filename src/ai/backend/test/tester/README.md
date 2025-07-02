# tester

This package provides the test runner and result management logic for the testing framework. The tester is responsible for executing testcases, managing concurrency, and exporting results.

The tester package is the orchestrator that brings together testcases, templates, and contexts to perform automated testing and collect results.

Unlike other test codes, the Tester package does not mock any components required for the Backend.AI environment or interactions with those components at all.

It performs actual integration tests by directly sending requests to the real Backend.AI manager and webserver.

## How to run tester-based integration tests in CLI

To run all the tests based on Tester, execute the following command.

```console
$ backend.ai test run-all
```

If you want to run only a specific test, execute the command as follows.

```console
$ backend.ai test run-test <test_name>
```

You can use the following command to see which test codes exist and which tests can be executed.

```console
$ backend.ai test get-all-specs
```

### `run` vs `run-all`

Some tests will only pass if certain configurations have been done in the development environment before running the `tester`.

These tests are marked with a tag named `required_XXX_configuration`.

The `tester.toml` file is configured by default to exclude these tests using the `exclude_tags`.

This is intended to help first-time users of the `tester` see all tests pass in their default development environment, reducing potential confusion.

You can try running only the tests that pass in the default development environment using the following command.

```console
$ backend.ai test run
```

If you want to ignore the exclude tags and run all tests, use the `run-all` command.


## Tester configuration (`tester.toml`)

To perform actual integration tests, various context configurations are required.
For example, you need to specify the endpoint configuration that determines which Manager and WebServer endpoints to send requests to.

By default, these values are set to the defaults for the local development environment, but you should modify the configuration if needed.

The default configuration file is located at `configs/tester/tester.toml`.
If needed, use the `--config-path` option when running tests to specify a different configuration.

