# Dummy agent

Dummy agents spawn dummy kernels.
Dummy kernels does not affect to agent's resource stat.
Dummy agent's kernels create one of two kind of code runner, `DummyCodeRunner` or `DummyFakeCodeRunner`. `DummyCodeRunner` initiates ZMQ sockets and implements abstract methods of `AbstractCodeRunner` that returns empty value or `None`.
`DummyFakeCodeRunner` does not initiate ZMQ sockets and it overrides all methods of `AbstractCodeRunner`.
We can mimic dummy agent's time-consuming steps by setting configuration file dummy-agent.toml. We can set the delay of each step by a tuple of 2 numbers that will convert to a range of random float or just a float that will convert to a delay time(sec).
dummy agents do not run `sync_container_lifecycles()`.

## How to use
Setup the config file of dummy agent like below.
```toml
[agent.intrinsic.cpu]
core-indexes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

[agent.intrinsic.memory]
size = 50000000000

[agent.delay]
scan-image = 0.1
pull-image = 0.1
destroy-kernel = 0.1
clean-kernel = 0.1
create-network = 0.1
destroy-network = 0.1


[agent.image]
already-have = []
need-to-pull = []
missing = []


[kernel-creation-ctx.delay]
prepare-scratch = 0.1
prepare-ssh = 0.1
spawn = 0.1
start-container = 2.0
mount-krunner = 0.1


[kernel]
use-fake-code-runner = true


[kernel.delay]
check-status = 0.1
get-completions = 0.1
get-logs = 0.1
interrupt-kernel = 0.1
start-service = 0.1
start-model-service = 0.1
shutdown-service = 0.1
commit = 10.0
get-service-apps = 0.1
accept-file = 0.1
download-file = 0.1
download-single = 0.1
list-files = 0.1
```
Then, set `agent.mode` value to `"dummy"`.
```toml
[agent]
mode = "dummy" # or backend = "dummy"
...
```

### How to set compute devices.
Dummy agents can use mock accelerators to set up heterogeneous computing devices, similar to how they do with *regular* agents. For more information, see `src/ai/backend/accelerator/mock`.
