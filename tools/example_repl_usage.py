"""
Example usage of Agent RPC Client in a REPL (IPython/Python).

This script demonstrates how to connect TO a running agent using StandaloneAgentClient.
The agent must already be running and binding to an address.

To use in IPython:
    $ ipython
    >>> %run tools/example_repl_usage.py
    >>> # Try the example functions
"""

from __future__ import annotations

import asyncio

from tools.agent_rpc_client import StandaloneAgentClient

# ==================== Configuration ====================

# Agent connection settings
AGENT_ADDR = "tcp://localhost:6001"  # Agent's bind address

# Optional authentication (set to None to disable)
MANAGER_PUBLIC_KEY = None  # bytes or None
MANAGER_SECRET_KEY = None  # bytes or None
AGENT_PUBLIC_KEY = None  # bytes or None

# Timeout settings
INVOKE_TIMEOUT = 30.0  # seconds
RPC_KEEPALIVE_TIMEOUT = 60  # seconds

# ==================== Connect to Agent ====================


async def create_agent_client() -> StandaloneAgentClient:
    """Create and connect to an agent client."""
    client = StandaloneAgentClient(
        AGENT_ADDR,
        manager_public_key=MANAGER_PUBLIC_KEY,
        manager_secret_key=MANAGER_SECRET_KEY,
        agent_public_key=AGENT_PUBLIC_KEY,
        invoke_timeout=INVOKE_TIMEOUT,
        rpc_keepalive_timeout=RPC_KEEPALIVE_TIMEOUT,
    )
    await client.connect()
    print(f"Connected to agent at {AGENT_ADDR}")
    return client


async def test_health() -> None:
    """Test connecting to agent and calling health."""
    print("\n=== Testing health() via client connection ===")
    async with StandaloneAgentClient(AGENT_ADDR) as client:
        health = await client.health()
        print(f"Health status: {health}")


async def test_hwinfo() -> None:
    """Test gathering hardware info from agent."""
    print("\n=== Testing gather_hwinfo() via client connection ===")
    async with StandaloneAgentClient(AGENT_ADDR) as client:
        hwinfo = await client.gather_hwinfo()
        print(f"Hardware info: {hwinfo}")


async def test_local_config() -> None:
    """Test getting local configuration from agent."""
    print("\n=== Testing get_local_config() via client connection ===")
    async with StandaloneAgentClient(AGENT_ADDR) as client:
        config = await client.get_local_config()
        print(f"Local config: {config}")


# ==================== Interactive Sessions ====================


async def interactive_session() -> StandaloneAgentClient:
    """
    Start an interactive session connecting to agent.

    This keeps a persistent connection open for multiple RPC calls.
    """
    print("\n=== Interactive session - Connecting to Agent ===")
    print(f"Connecting to agent at {AGENT_ADDR}...")

    client = await create_agent_client()
    print("\nClient connected and ready!")
    print("\nExample commands to try in IPython:")
    print("  >>> health = await client.health()")
    print("  >>> hwinfo = await client.gather_hwinfo()")
    print("  >>> config = await client.get_local_config()")
    print("  >>> gpu_map = await client.scan_gpu_alloc_map()")
    print("\nDon't forget to close when done:")
    print("  >>> await client.close()")

    return client


# ==================== Main Demo ====================


async def main() -> None:
    """Run a series of demo tests."""
    print("=" * 70)
    print("Agent RPC Client Demo")
    print("=" * 70)

    print(f"\nAgent Address: {AGENT_ADDR}")
    print(f"Authentication: {'Enabled' if AGENT_PUBLIC_KEY else 'Disabled'}")

    try:
        await test_health()
        await test_hwinfo()
        await test_local_config()
        print("\nTests completed successfully!")
    except Exception as e:
        print(f"\nError: {e}")
        print("(Make sure an agent is running and bound to the configured address)")

    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)


# ==================== Quick Reference ====================


def show_quick_reference() -> None:
    """Print a quick reference guide."""
    print("\n" + "=" * 70)
    print("QUICK REFERENCE")
    print("=" * 70)

    print("\n--- Connect to Agent ---")
    print("# Simple one-time call:")
    print("async with StandaloneAgentClient('tcp://localhost:6001') as client:")
    print("    result = await client.health()")

    print("\n# Persistent connection:")
    print("client = await create_agent_client()")
    print("result = await client.health()")
    print("await client.close()")

    print("\n--- Available RPC Methods ---")
    print("Health & Monitoring:")
    print("  - health(), gather_hwinfo(), ping_kernel()")
    print("Image Management:")
    print("  - check_and_pull(), purge_images(), push_image()")
    print("Kernel Lifecycle:")
    print("  - create_kernels(), destroy_kernel(), restart_kernel()")
    print("Kernel Operations:")
    print("  - execute(), interrupt_kernel(), get_completions()")
    print("File Operations:")
    print("  - upload_file(), download_file(), list_files()")
    print("Configuration:")
    print("  - get_local_config(), update_scaling_group()")
    print("GPU & Resources:")
    print("  - scan_gpu_alloc_map()")
    print("Agent Control:")
    print("  - shutdown_agent(), reset_agent()")

    print("\n" + "=" * 70)


# ==================== IPython Integration ====================

# When running in IPython, make helper functions available globally
try:
    get_ipython()  # type: ignore
    IN_IPYTHON = True
except NameError:
    IN_IPYTHON = False

if IN_IPYTHON:
    print("\n" + "=" * 70)
    print("IPython REPL Mode - Agent RPC Tools")
    print("=" * 70)

    print("\nAvailable Functions:")
    print("  - test_health()         # Test health check")
    print("  - test_hwinfo()         # Test hardware info gathering")
    print("  - test_local_config()   # Test local config retrieval")
    print("  - interactive_session() # Returns persistent client")

    print("\nUtilities:")
    print("  - create_agent_client()  # Manual client creation")
    print("  - show_quick_reference() # Show usage examples")

    print("\nConfiguration:")
    print(f"  AGENT_ADDR = '{AGENT_ADDR}'")
    print("  (Modify this variable to change the agent address)")

    print("\n" + "=" * 70)
    print("\nTip: Run show_quick_reference() for code examples!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    # Run the demo when executed as a script
    asyncio.run(main())
