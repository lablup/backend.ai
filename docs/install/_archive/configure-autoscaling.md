# Configure Autoscaling

Autoscaling strategies may vary cluster by cluster.
Here we introduce a brief summary of high-level guides.
(More details about configuring Backend.AI will follow soon.)

## ASG (Auto-scaling Group)

AWS and other cloud providers offer auto-scaling groups so that they control the number of VM instances sharing the same base image within certain limits depending on the VMs' CPU utilization or other resource metrics.
You could use this model for Backend.AI, but we recommend some customization due to the following reasons:

* Backend.AI's kernels are allocated a fixed and isolated amount of resources even when they do not use that much. So simple resource metering may expose "how busy" the spawned kernels are but not "how many" kernels are spwned. In the perspective of Backend.AI's scheduler, the latter is much more important.
* Backend.AI tries to maintain low latency when spawning new compute sessions. This means that it requires to keep a small number of VM instances to be at a "hot" ready state -- maybe just running idle ones or stopped ones for fast booting. If the cloud provider supports such fine-grained control, it is best to use their options. We are currently under development of Backend.AI's own fine-grained scaling.
* The Backend.AI scheduler treats GPUs as the first-class citizen like CPU cores and main memory for its capacity planning. Traditional auto-scaling metrics often miss this, so you need to set up a custom metric using vendor-specific ways.