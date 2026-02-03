from __future__ import annotations

import json
import os
from asyncio import subprocess
from typing import ClassVar, TypedDict

import aiohttp


class TPUDeviceProps(TypedDict):
    hw_location: str
    memory_size: int
    model_name: str


class libtpu:
    zone: ClassVar[str | None] = None

    @classmethod
    async def _run_ctpu(cls, cmd: list[str]) -> str:
        if not cls.zone:
            try:
                proc = await subprocess.create_subprocess_exec(
                    "gcloud",
                    "config",
                    "list",
                    '--format="json"',
                    stdout=subprocess.PIPE,
                )
                out, _ = await proc.communicate()
            except FileNotFoundError as e:
                raise ImportError("Gcloud SDK is not available!") from e
            config_json = json.loads(out)
            if zone := config_json.get("compute", {}).get("region"):
                cls.zone = zone
            else:
                try:
                    async with (
                        aiohttp.ClientSession() as sess,
                        sess.get(
                            "http://metadata.google.internal/computeMetadata/v1/instance/zone",
                            headers={"Metadata-Flavor": "Google"},
                        ) as resp,
                    ):
                        resp_body = await resp.text()
                        zone = resp_body.split("/")[-1]
                        cls.zone = zone
                except aiohttp.ClientError as e:
                    raise ImportError(
                        "Could not detect Gcloud zone automatically. Please set default gcloud zone."
                    ) from e
        else:
            zone = cls.zone
        try:
            proc = await subprocess.create_subprocess_exec(
                "gcloud",
                cmd,
                env={**os.environ, "CLOUDSDK_COMPUTE_ZONE": zone},
                stdout=subprocess.PIPE,
            )
            out, _ = await proc.communicate()
        except FileNotFoundError as e:
            raise ImportError("Gcloud SDK is not available!") from e
        return out.decode()

    @classmethod
    async def get_device_count(cls) -> int:
        cmd = ["compute", "tpus", "list", "--format", "value(name)", "--filter", "state:READY"]
        ret = await cls._run_ctpu(cmd)
        devices_info = ret.strip().splitlines()
        return len(devices_info)

    @classmethod
    async def get_device_name(cls, dev_idx: int) -> str:
        cmd = ["compute", "tpus", "list", "--format", "value(name)", "--filter", "state:READY"]
        ret = await cls._run_ctpu(cmd)
        devices_info = ret.strip().splitlines()
        return devices_info[dev_idx].strip()

    @classmethod
    async def get_device_props(cls, dev_name: str) -> TPUDeviceProps:
        cmd = ["compute", "tpus", "describe", dev_name, "--format", "json"]
        ret = await cls._run_ctpu(cmd)

        if ret == "":
            raise RuntimeError("TPU not found")

        tpu_info = json.loads(ret)
        if tpu_info["state"] != "READY":
            raise RuntimeError("TPU not ready for computation")

        tpu_version, cores = tpu_info["acceleratorType"].split("-")[:2]

        # v2 TPU has 8GiB memory for each core
        # v3 TPU has 16GiB for each
        memory_size = (
            int(cores) * 16 * 1024 * 1024 if tpu_version == "v3" else int(cores) * 8 * 1024 * 1024
        )

        return TPUDeviceProps(
            hw_location=tpu_info["name"].split("/")[-1],
            memory_size=memory_size,
            model_name=f"Google Cloud TPU {tpu_version} ({cores} cores)",
        )
