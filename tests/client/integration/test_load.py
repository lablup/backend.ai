"""
A standalone script to generate some loads to the public API server.
It assumes that you have already configured the access key and secret key
as environment variables.
"""

import logging
import multiprocessing
import secrets
import time
from statistics import mean, median, stdev

import pytest

from ai.backend.client.func.session import ComputeSession

# module-level marker
pytestmark = pytest.mark.integration

log = logging.getLogger("ai.backend.client.test.load")

sample_code = """
import os
print('ls:', os.listdir('.'))
with open('test.txt', 'w') as f:
    f.write('hello world')
"""

sample_code_julia = """
println("wow")
"""


def print_stat(msg, times_taken):
    print(
        "{}: mean {:.2f} secs, median {:.2f} secs, stdev {:.2f}".format(
            msg,
            mean(times_taken),
            median(times_taken),
            stdev(times_taken),
        )
    )


def run_create_kernel(_idx):
    begin = time.monotonic()
    try:
        k = ComputeSession.get_or_create("python3")
        ret = k.kernel_id
    except Exception:
        log.exception("run_create_kernel")
        ret = None
    finally:
        end = time.monotonic()
    t = end - begin
    return t, ret


def create_kernels(concurrency, parallel=False):
    kernel_ids = []
    times_taken = []

    if parallel:
        pool = multiprocessing.Pool(concurrency)
        results = pool.map(run_create_kernel, range(concurrency))
        for t, kid in results:
            times_taken.append(t)
            kernel_ids.append(kid)
    else:
        for _idx in range(concurrency):
            t, kid = run_create_kernel(_idx)
            times_taken.append(t)
            kernel_ids.append(kid)

    print_stat("create_kernel", times_taken)
    return kernel_ids


def run_execute_code(kid):
    if kid is not None:
        begin = time.monotonic()
        console = []
        run_id = secrets.token_hex(8)
        while True:
            result = ComputeSession(kid).execute(run_id, sample_code)
            console.extend(result["console"])
            if result["status"] == "finished":
                break
        stdout = "".join(rec[1] for rec in console if rec[0] == "stdout")
        end = time.monotonic()
        print(stdout)
        return end - begin
    return None


def execute_codes(kernel_ids, parallel=False):
    times_taken = []

    if parallel:
        pool = multiprocessing.Pool(len(kernel_ids))
        results = pool.map(run_execute_code, kernel_ids)
        for t in results:
            if t is not None:
                times_taken.append(t)
    else:
        for kid in kernel_ids:
            t = run_execute_code(kid)
            if t is not None:
                times_taken.append(t)

    print_stat("execute_code", times_taken)


def run_restart_kernel(kid):
    # 2nd params is currently ignored.
    if kid is not None:
        begin = time.monotonic()
        ComputeSession(kid).restart()
        end = time.monotonic()
        return end - begin
    return None


def restart_kernels(kernel_ids, parallel=False):
    times_taken = []

    if parallel:
        pool = multiprocessing.Pool(len(kernel_ids))
        results = pool.map(run_restart_kernel, kernel_ids)
        for t in results:
            if t is not None:
                times_taken.append(t)
    else:
        for kid in kernel_ids:
            t = run_restart_kernel(kid)
            if t is not None:
                times_taken.append(t)

    print_stat("restart_kernel", times_taken)


def run_destroy_kernel(kid):
    if kid is not None:
        begin = time.monotonic()
        ComputeSession(kid).destroy()
        end = time.monotonic()
        return end - begin
    return None


def destroy_kernels(kernel_ids, parallel=False):
    times_taken = []

    if parallel:
        pool = multiprocessing.Pool(len(kernel_ids))
        results = pool.map(run_destroy_kernel, kernel_ids)
        for t in results:
            if t is not None:
                times_taken.append(t)
    else:
        for kid in kernel_ids:
            t = run_destroy_kernel(kid)
            if t is not None:
                times_taken.append(t)

    print_stat("destroy_kernel", times_taken)


@pytest.mark.parametrize(
    "concurrency,parallel,restart",
    [
        (5, False, False),
        (5, True, False),
        (5, False, True),
        (5, True, True),
    ],
)
def test_high_load_requests(capsys, defconfig, concurrency, parallel, restart):
    """
    Tests creation and use of multiple concurrent kernels in various ways.

    NOTE: This test may fail if your system has too less cores compared to the
    given concurrency.  The exact number of cores required is determined by the
    Python3 kernel's resource requirements (CPU slots).

    NOTE: This test may occasionally fail if it takes too long time to destroy
    Docker containers in the manager because the resources occupation is
    restored after container destruction but the destroy API returns after
    stopping containers but before they are actually destroyed.
    We have inserted some small delay to work-around this.
    Running this tests with different parameters without no delays between
    parameter sets would cause "503 Service Unavailable" errors as it will
    quickly saturate the resource limit of the developer's PC.
    """

    # Show stdout for timing statistics
    with capsys.disabled():
        print("waiting for previous asynchronous kernel destruction for 5 secs...")
        time.sleep(5)
        kids = create_kernels(concurrency, parallel)
        execute_codes(kids, parallel)
        if restart:
            restart_kernels(kids, parallel)
            execute_codes(kids, parallel)
        destroy_kernels(kids, parallel)
