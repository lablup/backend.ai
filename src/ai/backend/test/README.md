# Backend.AI Testing Toolkit

Automated test suites to validate an installation and integration of clients and servers


## How to run CLI-based integration test

If there is no configuration script named `env-tester.sh`, copy it from `sample-env-tester.sh` and check the configuration env.

```console
$ source env-tester.sh
$ backend.ai test run-cli
```

NOTE: The ENV script is parsed with `"^export (\w+)=(.*)$"` regex pattern line by line.
