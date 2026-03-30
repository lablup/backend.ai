---
Author: Joongi Kim (joongi@lablup.com)
Status: Draft
Created: 2025-11-16
Created-Version:
Target-Version:
Implemented-Version:
---

# Preemption of Low-priority Sessions

## Motivation

Currently we have a priority number in the range of 0..100 integer, whereas the default value is 10.
The scheduler schedules the pending sessions with the highest priority value first.
If there are still remaining resources, then it schedules the pending sessions with the next-highest priority value.

There are some use cases that we need to preempt already-running low-priority sessions to start the pending sessions with higher priority as quickliest as possible.

## Specification

### Configuration

| Field                  | Scope          | Default     | Description                                                                                                             |
| ---------------------- | -------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------- |
| `preemptible_priority` | Resource Group | 5           | The priority number threshold to make running sessions with the priority value lower or equivalent to this preemptible. |
| `preemption_order`     | Resource Group | "oldest"    | Preempt "oldest" or "newest" running sessions first when they have same (lower) priority.                               |
| `preemption_mode`      | Resource Group | "terminate" | Specify how to do preemption. Availalbe values: "terminate", "suspend".                                                 |

Since the scheduler runs in the resource group scope, this configuration should be per resource group.

Let's first implement `preemption_mode == "terminate"` first.
For `"suspend"`, see discussions below.

### Implementation

The scheduler determines if it needs to perform preemption as follows:

- There are not enough resources to schedule the pending session in the front of the job queue.
- There are running sessions with lower priority than the pending session in the front of the job queue.

When doing preemption, there may be multiple running sessions with same or different priority values to preempt.
Choose the preempted sessions by the following order, until we have enough released resources to start the pending session:

* Lowest priority value
* The job start time
  - Oldest first or newest first depending on `preemption_order` configuration

### Frontend and UI

* WebUI needs to be able to set priority values when creating sessions
  when the resource policy allows.

### Resource Policies

* Per-project resource policy and user resource policies should be able to:
  - The default priority
  - Enable/disable ability to change priority
  - The priority value range they can set when enabled


## Discussion

### Similarity and Differences to Slurm

Slurm has a concept of [preemption](https://slurm.schedmd.com/preempt.html) which works like the preemption logic described in this BEP.

Instead of having priority value per individual job,
Slurm has the concept of partitions and map `PriorityTier` and `PreemptMode` configurations to them and put jobs into partitions.
If a job is created inside "preemptible" partitions,
it can be terminated by the scheduler when there are resource competition.

In Backend.AI, _resource groups_ are similar to Slurm's partitions, but it is a non-overlapping set of physical or logical nodes.
A phsyical node may be partitioned into multiple logical nodes with disjoint compute resources.

The preemptible partition could be simulated by setting the priority value of pending sessions and adjusting `preemptible_priority`.

### Suspension and resumption of preempted sessions

> [!WARNING]
> We need discussion on this section.

When `preemption_mode == "suspend"`,  we may need to store the session state/metadata and resume it afterwards.

The primary use case will be:

* The preempted session is a batch job, which has internal checkpointing and resumption mechanisms.

Though, it may not apply when:

* The preempted session is an inference job
  - The autoscaling mechanism automatically restores the replicas when there are released resources.
  - This automatic restoration is also subject to the priority of the inference deployment.
* The preempted session is an interactive job, which needs human intervention to resume work.

If we want to resume a suspended session, we need to keep its configuration and metadata when terminated,
and make it a pending session again when there are released resources.
We need to define the conditions and how to achieve this.

**Potential approaches:**

* Terminate the containers but keep the session object by marking it "suspended".
  Re-enqueue the session when resumed and let the scheduler create a fresh new session using the same configuration.
* Stop the container and marking the session "suspended", but don't remove it.
  This allows the resumed/restarted container to reuse any local resource (e.g., scratch directories).
