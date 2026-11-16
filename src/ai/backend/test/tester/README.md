# tester

This package provides the test runner and result management logic for the testing framework. The tester executes testcases, manages concurrency and exports results.

The tester package is the orchestrator that brings together testcases, templates and contexts to perform automated testing and collect results.

Unlike other test code, the tester package does not mock any component that the Backend.AI environment requires, nor any interaction with those components at all.

It performs actual integration tests by sending requests directly to the real Backend.AI manager and webserver.

## How to run tester-based integration tests in CLI

### Basic test execution

The most commonly used command is `run`, which executes tests that are expected to pass in a default development environment:

```console
$ backend.ai test run
```

This command automatically excludes tests that require special environment configurations, so it suits first-time users and standard development workflows.

### Running all tests

To run all available tests, including those that require special configurations, use:

```console
$ backend.ai test run-all
```

### Running specific tests

To run one specific test, execute the command as follows:

```console
$ backend.ai test run-test <test_name>
```

You can use the following command to see which test codes exist and which tests can be executed:

```console
$ backend.ai test get-all-specs
```

### Understanding `run` vs `run-all`

Some tests pass only after certain configurations have been done in the development environment before the `tester` runs. These tests carry a tag named `required_XXX_configuration`.

The tester configuration file excludes these tests through `exclude_tags` when you use the `run` command. This helps a first-time user of the `tester` see all tests pass in their default development environment and reduces potential confusion.

If you want to ignore the `exclude_tags` and run all tests, use the `run-all` command.


## Tester configuration (`tester.toml`)

To perform actual integration tests, various context configurations are required.
For example, you need to specify, in the `endpoint` configuration, the manager and webserver addresses to which requests are sent.

By default, these values are set to the defaults for the local development environment, but you should change the configuration if needed.

The default configuration file is located at `configs/tester/tester.toml`.
If needed, use the `--config-path` option when running tests to specify a different configuration.

### Tags

This section provides guidance on tags that require additional environment setup in order to pass.

<!-- #### `required_single_node_multi_container_configuration` -->

---

#### `required_multi_node_multi_container_configuration`

The nodes must be connected, for example, through a Docker Swarm setup.
Set `swarm-enabled` to true in the `agent.toml` file, and initialize the swarm on the manager node.
Then, join the agent nodes to the swarm.

---

#### `required_container_registry_configuration`
The project used in the test must have the `container_registry` setting configured.
Tests with this tag operate using the image and the configured container registry.
