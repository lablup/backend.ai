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

### Example of dummy compute device settings.
1. cuda.device
```
...

[dummy.agent.device-plugins]
devices = [
    { device-id = "device-id", device-name = "cuda", allocation-mode = "discrete" }
]

[dummy.agent.device-plugins.metadata]
display-unit = "cuda-device"
display-icon = "cuda-device"
human-readable-name = "Cuda device"
number-format = {}

...
```

2. cuda.shares
```
...

[dummy.agent.device-plugins]
devices = [
    { device-id = "device-id", device-name = "cuda", allocation-mode = "fractional" }
]

[dummy.agent.device-plugins.metadata]
display-unit = "cuda-shares"
display-icon = "cuda-shares"
human-readable-name = "Cuda shares"
number-format = {}

...
```
