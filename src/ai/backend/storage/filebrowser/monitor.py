import asyncio
import time

import aiotools

from ai.backend.storage.context import Context

from .filebrowser import destroy_container, get_filebrowsers, get_network_stats


async def network_monitor(
    ctx: Context,
    container_id: str,
    activity_check_freq: int,
    activity_check_timeout: int,
) -> None:
    start_time = time.monotonic()
    network_window = []
    while True:
        current_time = time.monotonic()
        try:
            stats = await get_network_stats(container_id)
        except Exception as e:
            print("Failed to get network stats ", e)
            break
        network_total_transfer = stats[0] + stats[1]
        network_window.append(network_total_transfer)
        if current_time - start_time > activity_check_timeout:
            network_utilization_change = network_window[-1] - network_window[0]
            if network_utilization_change == 0:
                start_time = current_time
                try:
                    await destroy_container(ctx, container_id)
                except Exception as e:
                    print(
                        f"Failure to destroy container based on networking timeout {container_id}",
                        e,
                    )
                    break
            else:
                network_window = []
                start_time = current_time
        await asyncio.sleep(activity_check_freq)


async def idle_timeout_monitor(
    ctx: Context,
    container_id: str,
    idle_timeout: int,
) -> None:
    start_time = time.monotonic()
    while True:
        current_time = time.monotonic()
        if current_time - start_time >= idle_timeout:
            try:
                await destroy_container(ctx, container_id)
            except Exception as e:
                print(
                    f"Failure to destroy container based on Idle timeout {container_id}",
                    e,
                )
                break
        await asyncio.sleep(1)


async def keep_monitors_running(ctx: Context) -> None:
    idle_timeout = ctx.local_config["filebrowser"]["idle_timeout"]
    activity_check_freq = ctx.local_config["filebrowser"]["activity_check_freq"]
    activity_check_timeout = ctx.local_config["filebrowser"]["activity_check_timeout"]
    network_monitored_list = []
    idle_time_monitored_list = []
    while True:
        browsers = await get_filebrowsers()
        if len(browsers) > 0:
            async with aiotools.TaskGroup() as tg:
                for browser in browsers:
                    if browser not in network_monitored_list:
                        network_monitored_list.append(browser)
                        tg.create_task(
                            network_monitor(
                                ctx,
                                browser,
                                activity_check_freq,
                                activity_check_timeout,
                            ),
                        )
                    if (idle_timeout is not None) and (browser not in idle_time_monitored_list):
                        idle_time_monitored_list.append(browser)
                        tg.create_task(idle_timeout_monitor(ctx, browser, idle_timeout))
        await asyncio.sleep(10)
