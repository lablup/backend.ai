# backend.ai-accelerator-mock

A mockup plugin for accelerators

This plugin deceives the agent and manager to think as if there are accelerator devices.
The configuration follows `mock-accelerator.toml` placed in the same location of `agent.toml`.
Please refer the sample configurations in the `configs/accelerator` directory and copy one of them as a starting point.

The statistics are randomly generated in reasonable ranges, but it may seem like "jumping around" because there is no smoothing mechanism of generated values.
The configurations for fractional/discrete mode, fraction size, and device masks in etcd are exactly same as the original plugin.

## Notes when setting up mock CUDA devices

The containers are created without any real CUDA device mounts but with `BACKENDAI_MOCK_CUDA_DEVICES` and `BACKENDAI_MOCK_CUDA_DEVICE_COUNT` environment variables.
Since the manager does not know if the reported devices are real or not, you can start any CUDA-only containers (but of course they won't work as expected).
