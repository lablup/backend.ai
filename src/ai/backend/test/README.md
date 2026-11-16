# Backend.AI Testing Toolkit

Automated test suites that validate an installation and the integration of clients and servers.

## How to run a CLI-based integration test

If there is no configuration script named `env-tester.sh`, copy it from `sample-env-tester.sh` and check the configuration environment variables.

```console
$ source env-tester.sh
$ backend.ai test run-cli
```

The environment script is parsed one line at a time with the `"^export (\w+)=(.*)$"` regex pattern.
