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

### `tester.toml`

To perform actual integration tests, various context configurations are required.
For example, you need to specify the endpoint configuration that determines which Manager and WebServer endpoints to send requests to.

By default, these values are set to the defaults for the local development environment, but you should modify the configuration if needed.

The default configuration file is located at `configs/tester/tester.toml`.
If needed, use the `--config-path` option when running tests to specify a different configuration.

