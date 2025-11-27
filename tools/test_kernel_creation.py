"""
Test kernel creation on Kubernetes agent.

Usage in IPython:
    $ PYTHONPATH=src/ ipython
    >>> %run tools/test_kernel_creation.py

    # Create a simple kernel (CPU + memory only)
    >>> result = await test_create_simple_kernel()

    # Create a kernel with GPU
    >>> result = await test_create_gpu_kernel()

    # Execute code in a running kernel
    >>> await test_execute_code(session_id, kernel_id, "print('hello')")
    >>> await test_execute_code(session_id, kernel_id, "import torch; print(torch.cuda.is_available())")

    # Check if agent can detect GPUs
    >>> await test_check_gpu()

    # Destroy a kernel
    >>> await test_destroy_kernel(session_id, kernel_id)

    # Full lifecycle test (create, execute, destroy)
    >>> await test_full_lifecycle()
"""

from __future__ import annotations

import uuid
from typing import Any

from tools.agent_rpc_client import StandaloneAgentClient

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import KernelId

# Agent connection
AGENT_ADDR = "tcp://10.100.66.2:30001"


async def test_create_simple_kernel(with_gpu: bool = False) -> dict[str, Any]:
    """
    Create a simple Python kernel for testing.

    Args:
        with_gpu: If True, request 1 GPU for the kernel.

    Returns the kernel creation result.
    """
    # Generate unique IDs
    session_uuid = uuid.uuid4()
    session_id = str(session_uuid)
    kernel_uuid = uuid.uuid4()
    kernel_id_str = str(kernel_uuid)
    owner_user_uuid = uuid.uuid4()
    owner_user_id = str(owner_user_uuid)

    print("Creating kernel:")
    print(f"  Session ID: {session_id}")
    print(f"  Kernel ID: {kernel_id_str}")

    # Simple Python kernel configuration
    # Using NVIDIA NGC PyTorch image for ARM64 + CUDA (Grace Blackwell GB10)
    kernel_config: dict[str, Any] = {
        "lang": "python",
        "image": {
            "canonical": "nvidia/pytorch:24.08-py3",
            "project": None,
            "architecture": "aarch64",  # ARM64
            "digest": "",
            "repo_digest": None,
            "registry": {
                "name": "nvcr.io",
                "url": "https://nvcr.io",
            },
            "labels": {
                "ai.backend.base-distro": "ubuntu22.04",
                "ai.backend.runtime-type": "python",
                "ai.backend.runtime-path": "/usr/bin/python",
            },
            "is_local": False,
            "auto_pull": "digest",
        },
        "kernel_id": kernel_id_str,
        "session_id": session_id,
        "owner_user_id": owner_user_id,
        "owner_project_id": None,
        "network_id": "test-network",
        "auto_pull": "digest",
        "session_type": "interactive",
        "cluster_mode": "single-node",
        "cluster_role": "main",
        "cluster_idx": 0,
        "cluster_hostname": f"kernel-{kernel_id_str}",
        "local_rank": 0,
        "uid": 1000,
        "main_gid": 1000,
        "supplementary_gids": [],
        "resource_slots": {
            "cpu": "1",
            "mem": "1073741824",  # 1 GiB in bytes
            **({"cuda.device": "1"} if with_gpu else {}),
        },
        "resource_opts": {},
        "environ": {},
        "mounts": [],
        "package_directory": [],
        "idle_timeout": 600,
        "bootstrap_script": None,
        "startup_command": None,
        "internal_data": None,
        "preopen_ports": [],
        "allocated_host_ports": [],
        "scaling_group": "default",
        "agent_addr": AGENT_ADDR,
        "endpoint_id": None,
    }

    # Cluster info for single-node kernel
    cluster_info = {
        "mode": "single-node",
        "size": 1,
        "ssh_keypair": None,  # K8s agent requires this field (can be None)
    }

    # Image reference for NGC PyTorch (ARM64 + CUDA)
    image_refs = {
        KernelId(kernel_uuid): ImageRef.from_image_str(
            "nvidia/pytorch:24.08-py3",
            project=None,
            registry="nvcr.io",
            architecture="aarch64",
            is_local=False,
        )
    }

    async with StandaloneAgentClient(AGENT_ADDR) as client:
        print("\nCalling create_kernels RPC...")
        try:
            result = await client.create_kernels(
                session_id,
                [kernel_id_str],
                [kernel_config],
                cluster_info,
                image_refs,
            )
            print("\n✓ Kernel creation initiated!")
            print(f"Result: {result}")
            return result
        except Exception as e:
            print(f"\n✗ Kernel creation failed: {e}")
            raise


async def test_create_gpu_kernel() -> dict[str, Any]:
    """Create a kernel with 1 GPU allocated."""
    return await test_create_simple_kernel(with_gpu=True)


async def test_destroy_kernel(session_id: str, kernel_id: str) -> None:
    """Destroy a previously created kernel."""
    print("\nDestroying kernel:")
    print(f"  Session ID: {session_id}")
    print(f"  Kernel ID: {kernel_id}")

    async with StandaloneAgentClient(AGENT_ADDR) as client:
        try:
            await client.destroy_kernel(
                kernel_id,
                session_id,
                reason="test cleanup",
            )
            print("\n✓ Kernel destroyed (probably, check kubectl get pods)!")
        except Exception as e:
            print(f"\n✗ Kernel destruction failed: {e}")
            raise


async def test_execute_code(
    session_id: str,
    kernel_id: str,
    code: str,
    mode: str = "query",
) -> dict[str, Any]:
    """
    Execute code in a running kernel.

    Args:
        session_id: The session ID of the kernel.
        kernel_id: The kernel ID.
        code: The code to execute.
        mode: Execution mode - "query" for single expression, "batch" for multiple statements.

    Returns:
        Execution result containing stdout, stderr, media outputs, etc.

    Example:
        >>> result = await test_execute_code(session_id, kernel_id, "print('hello')")
        >>> print(result)
    """
    import uuid

    run_id = str(uuid.uuid4())

    print(f"\nExecuting code in kernel {kernel_id}:")
    print(f"  Mode: {mode}")
    print(f"  Code: {code[:100]}{'...' if len(code) > 100 else ''}")

    async with StandaloneAgentClient(AGENT_ADDR) as client:
        try:
            result = await client.execute(
                session_id=session_id,
                kernel_id=kernel_id,
                api_version=5,  # Current API version
                run_id=run_id,
                mode=mode,
                code=code,
                opts={},
                flush_timeout=10.0,
            )
            print("\n✓ Execution completed!")
            print(f"Result: {result}")
            return result
        except Exception as e:
            print(f"\n✗ Execution failed: {e}")
            raise


async def test_check_gpu() -> dict[str, Any]:
    """
    Check if the agent can detect GPUs.

    Returns available slot information including cuda.device if GPUs are present.
    """
    async with StandaloneAgentClient(AGENT_ADDR) as client:
        hwinfo = await client.gather_hwinfo()
        print("\nHardware Info:")
        print(f"  {hwinfo}")

        # Check for CUDA devices
        if "cuda" in hwinfo.get("accelerators", {}):
            cuda_info = hwinfo["accelerators"]["cuda"]
            print(f"\n✓ CUDA devices found: {len(cuda_info.get('devices', []))} GPU(s)")
            for dev in cuda_info.get("devices", []):
                print(f"    - {dev.get('model', 'Unknown')} ({dev.get('device_id', 'N/A')})")
        else:
            print("\n⚠ No CUDA devices detected")

        return hwinfo


async def test_full_lifecycle() -> None:
    """Test full kernel lifecycle: create, wait, destroy."""
    import asyncio

    # Create kernel
    result = await test_create_simple_kernel()

    # Extract IDs from result
    # The result structure may vary, adjust as needed
    session_id = result.get("session_id")
    kernel_id = result.get("kernel_id")

    if not session_id or not kernel_id:
        print("\n⚠ Could not extract session_id/kernel_id from result")
        print(f"Result keys: {result.keys()}")
        return

    # Wait for kernel to start
    print("\nWaiting 10 seconds for kernel to start...")
    await asyncio.sleep(10)

    # Execute a simple test
    try:
        exec_result = await test_execute_code(
            session_id,
            kernel_id,
            "import sys; print(f'Python {sys.version}')",
        )
        print(f"Execution result: {exec_result}")
    except Exception as e:
        print(f"Execution test failed: {e}")

    # Cleanup
    await test_destroy_kernel(session_id, kernel_id)


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_create_simple_kernel())
