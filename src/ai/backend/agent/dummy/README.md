# Dummy agent

Dummy agents spawn dummy kernels.
Dummy kernels does not affect to agent's resource stat.
Dummy agent's kernels create one of two kind of code runner, `DummyCodeRunner` or `DummyFakeCodeRunner`. `DummyCodeRunner` initiates ZMQ sockets and implements abstract methods of `AbstractCodeRunner` that returns empty value or `None`.
`DummyFakeCodeRunner` does not initiate ZMQ sockets and it overrides all methods of `AbstractCodeRunner`.
We can mimic dummy agent's time-consuming steps by setting configuration file dummy-agent.toml. We can set the delay of each step by a tuple of 2 numbers that will convert to a range of random float or just a float that will convert to a delay time(sec).
dummy agents do not run `sync_container_lifecycles()`.

## How to use
Setup the config file of dummy agent and run. You can check agent's `sample.toml`.
You **should** set `agent.mode` value to `"dummy"` first.

### How to set compute devices.
Dummy agents can use mock accelerators to set up heterogeneous computing devices, similar to how they do with *regular* agents. For more information, see `src/ai/backend/accelerator/mock`.
