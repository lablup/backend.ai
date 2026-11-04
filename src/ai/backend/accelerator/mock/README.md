# backend.ai-accelerator-mock

A mockup plugin for accelerators

<<<<<<< HEAD
This plugin deceives the agent and manager to think as if there are accelerator devices.
The configuration follows `mock-accelerator.toml` placed in the same location of `agent.toml`.
Please refer the sample configurations in the `configs/accelerator` directory and copy one of them as a starting point.
=======
The plugin makes the Agent and the Manager see accelerator devices that are not present.
The configuration comes from `mock-accelerator.toml` in the same directory as `agent.toml`.
See the sample configurations in the `configs/accelerator` directory and copy one as a starting point.
The agent loads the plugin only when `allow-compute-plugins` in `agent.toml` lists `ai.backend.accelerator.mock`.
>>>>>>> 4db0c0e29 (fix(BA-8919): require an explicit allow for the mock accelerator plugin (#16405))

The statistics are randomly generated in reasonable ranges, but it may seem like "jumping around" because there is no smoothing mechanism of generated values.
The configurations for fractional/discrete mode, fraction size, and device masks in etcd are exactly same as the original plugin.

## Notes when setting up mock CUDA devices

The containers are created without any real CUDA device mounts but with `BACKENDAI_MOCK_CUDA_DEVICES` and `BACKENDAI_MOCK_CUDA_DEVICE_COUNT` environment variables.
Since the manager does not know if the reported devices are real or not, you can start any CUDA-only containers (but of course they won't work as expected).
