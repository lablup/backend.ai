import inspect
from time import monotonic

import zmq
import zmq.asyncio
from jupyter_client import AsyncKernelClient


async def aexecute_interactive(
    kernel_client: AsyncKernelClient,
    code: str,
    silent=False,
    store_history=True,
    user_expressions=None,
    allow_stdin=None,
    stop_on_error=True,
    timeout=None,
    output_hook=None,
    stdin_hook=None,
):
    """Async version of jupyter_client's execute_interactive method.

    https://github.com/jupyter/jupyter_client/blob/9f1c379/jupyter_client/client.py#L415
    """
    if not kernel_client.iopub_channel.is_alive():
        raise RuntimeError("IOPub channel must be running to receive output")
    if allow_stdin is None:
        allow_stdin = kernel_client.allow_stdin
    if allow_stdin and not kernel_client.stdin_channel.is_alive():
        raise RuntimeError("stdin channel must be running to allow input")
    msg_id = kernel_client.execute(  # not async!
        code,
        silent=silent,
        store_history=store_history,
        user_expressions=user_expressions,
        allow_stdin=allow_stdin,
        stop_on_error=stop_on_error,
    )
    stdin_hook = stdin_hook if stdin_hook else kernel_client._stdin_hook_default
    output_hook = output_hook if output_hook else kernel_client._output_hook_default

    # set deadline based on timeout
    if timeout is not None:
        deadline = monotonic() + timeout
    else:
        timeout_ms = None

    poller = zmq.asyncio.Poller()
    iopub_socket = kernel_client.iopub_channel.socket
    poller.register(iopub_socket, zmq.POLLIN)
    if allow_stdin:
        stdin_socket = kernel_client.stdin_channel.socket
        poller.register(stdin_socket, zmq.POLLIN)
    else:
        stdin_socket = None

    # Wait for zmq events and handle them
    while True:
        if timeout is not None:
            timeout = max(0, deadline - monotonic())
            timeout_ms = 1e3 * timeout
        events = dict(await poller.poll(timeout_ms))
        if not events:
            raise TimeoutError("Timeout waiting for output")
        if stdin_socket in events:
            req = await kernel_client.stdin_channel.get_msg(timeout=0)
            if inspect.iscoroutinefunction(stdin_hook):
                await stdin_hook(req)
            else:
                stdin_hook(req)
            continue
        if iopub_socket not in events:
            continue

        msg = await kernel_client.iopub_channel.get_msg(timeout=0)

        if msg["parent_header"].get("msg_id") != msg_id:
            # not from my request
            continue
        if inspect.iscoroutinefunction(output_hook):
            await output_hook(msg)
        else:
            output_hook(msg)

        # stop on idle
        if msg["header"]["msg_type"] == "status" and msg["content"]["execution_state"] == "idle":
            break

    # output is done, get the reply
    if timeout is not None:
        timeout = max(0, deadline - monotonic())
    return await kernel_client._recv_reply(msg_id, timeout=timeout)
