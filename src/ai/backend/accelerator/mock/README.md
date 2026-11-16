# backend.ai-accelerator-mock

A mock accelerator plugin

The plugin makes the Agent and the Manager see accelerator devices that are not present.
The configuration comes from `mock-accelerator.toml` in the same directory as `agent.toml`.
See the sample configurations in the `configs/accelerator` directory and copy one as a starting point.
The agent loads the plugin only when `allow-compute-plugins` in `agent.toml` lists `ai.backend.accelerator.mock`.

Statistics are random within reasonable ranges. Generated values have no smoothing, so they can look like they jump around.
The configuration for fractional and discrete modes, fraction size, and device masks in etcd matches the original plugin exactly.

## Notes when setting up mock CUDA devices

Containers are created without a real CUDA device mount and with the `BACKENDAI_MOCK_CUDA_DEVICES` and `BACKENDAI_MOCK_CUDA_DEVICE_COUNT` environment variables.
The Manager does not know whether the reported devices are real, so you can start any CUDA-only container, but it does not work as expected.
