
On the clouds, we highly recommend using vendor-provided GPU-optimized instance types (e.g., p2/p3 series on AWS) and GPU-optimized virtual machine images which include ready-to-use CUDA drivers and configurations.

Since Backend.AI's kernel container images ship all the necessary libraries and 3rd-party computation packages, you may choose the light-weight "base" image (e.g., Amazon Deep Learning *Base* AMI) instead of full-featured images (e.g., Amazon Deep Learning Conda AMI).

Manually install CUDA at on-premise GPU servers
-----------------------------------------------

Please search for this topic on the Internet, as Linux distributions often provide their own driver packages and optimized method to install CUDA.

To download the driver and CUDA toolkit directly from NVIDIA, `visit here <https://developer.nvidia.com/cuda-downloads>`_.

Let Backend.AI to utilize GPUs
------------------------------

If an agent server has properly configured nvidia-docker (ref: [[Install Docker]]) with working host-side drivers and the agent's Docker daemon has GPU-enabled kernel images, there is *nothing* to do special.
Backend.AI tracks the GPU capacity just like CPU cores and RAM, and uses that information to schedule and assign GPU-enabled kernels.
