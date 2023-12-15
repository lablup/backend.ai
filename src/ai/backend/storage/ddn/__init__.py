import asyncio
from pathlib import Path
from subprocess import CalledProcessError
from typing import Any, Final, FrozenSet, Mapping

from ai.backend.common.types import QuotaScopeID
from ai.backend.storage.exception import QuotaScopeNotFoundError

from ..abc import CAP_QUOTA, CAP_VFOLDER, AbstractQuotaModel
from ..subproc import run
from ..types import Optional, QuotaConfig, QuotaUsage
from ..vfs import BaseQuotaModel, BaseVolume

PROJECT_ID_FILE_NAME: Final = "project_id"


class EXAScalerQuotaModel(BaseQuotaModel):
    def __init__(self, mount_path: Path, local_config: Mapping[str, Any]) -> None:
        self.local_config = local_config
        super().__init__(mount_path)

    async def _set_quota_by_pool(self, quota_scope_id: QuotaScopeID, limit_bytes: int) -> None:
        fs_name = self.local_config["fs_name"]
        pool_name = f"{fs_name}.{str(quota_scope_id)}"
        qspath = self.mangle_qspath(quota_scope_id)
        if not qspath.exists():
            raise QuotaScopeNotFoundError

        # Set quota
        try:
            await run([
                b"lfs",
                b"setquota",
                b"--pool",
                pool_name,
                b"-B",
                str(limit_bytes),
                str(qspath),
            ])
        except CalledProcessError as e:
            raise RuntimeError(f"'lfs setquota' command failed: {e.stderr}")

    # async def _set_quota_by_project(self, quota_scope_id: QuotaScopeID, limit_bytes: int) -> None:
    #     qspath = self.mangle_qspath(quota_scope_id)
    #     if not qspath.exists():
    #         raise QuotaScopeNotFoundError
    #     fs_name = self.local_config["fs_name"]

    async def create_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        options: Optional[QuotaConfig] = None,
        extra_args: Optional[dict[str, Any]] = None,
    ) -> None:
        # AWS example
        # Associate directory with project
        "lfs project -p 100 -r -s /mnt/fsxfs/dir1"
        "lfs setquota -p 250 -b 307200 -B 309200 -i 10000 -I 11000 /mnt/fsx"

        # doc example
        "lfs setquota -p 111 -B100T /mnt/testfs"
        "lfs setquota -p 111 --pool ddn_ssd -b 10G -B 11G -i 0 -I 0 /mnt/testfs"
        "lfs project -p 111 -s /mnt/testfs/111"
        "lfs project -d /mnt/testfs/111"  # to check directory metadata? the below line could be result
        "111 P /mnt/testfs/111"

        r"lfs setquota {-u|--user|-g|--group|-p} {<uname>|<gname>} [--pool <pool_name] \ [-b <block-softlimit>] [-B <block_hardlimit>] [-i <inode_softlimit>] [-I <inode_hardlimit>] <fs_mount_point>"

        qspath = self.mangle_qspath(quota_scope_id)
        fs_name = self.local_config["fs_name"]
        pool_name = f"{fs_name}.{str(quota_scope_id)}"

        # Create new pool
        try:
            await run([
                b"lctl",
                b"pool_new",
                pool_name,
            ])
        except CalledProcessError as e:
            raise RuntimeError(f"'lctl pool_new' command failed: {e.stderr}")

        try:
            await run([
                b"lctl",
                b"pool_add",
                pool_name,
                f"{self.local_config['ost_list']}",
            ])
        except CalledProcessError as e:
            raise RuntimeError(f"'lctl pool_add' command failed: {e.stderr}")

        # Assign pool to an directory
        try:
            await run([
                b"lfs",
                b"setstripe",
                b"-p",
                f"{fs_name}.{qspath}",
                qspath,
            ])
        except CalledProcessError as e:
            raise RuntimeError(f"'lfs setstripe' command failed: {e.stderr}")

        if options is not None:
            await self._set_quota_by_pool(quota_scope_id, options.limit_bytes)

    async def describe_quota_scope(self, quota_scope_id: QuotaScopeID) -> Optional[QuotaUsage]:
        """
        $ lfs quota -p <projectId> --pool <pool_name> -v <fs_mount_point>

        Disk quotas for user bob (uid 500):
        Filesystem  kbytes  quota   limit   grace       fies    quota   limit   grace
        /mnt/testfs 30400*  30400   30900   6d23h49m12s 10101*  10000   11000
        #                           `limit` is hard limit
        #                   `quota` is soft limit
        6d23h59m50s
        testfs-MDT0000_UUID
        testfs-OST0000_UUID
        testfs-OST0001_UUID
        ...
        Total allocated inode limit: 11000, total allocated block limit: 30900
        """

        qspath = self.mangle_qspath(quota_scope_id)
        fs_name = self.local_config["fs_name"]
        pool_name = f"{fs_name}.{str(quota_scope_id)}"

        proc = await asyncio.create_subprocess_exec(
            b"lfs",
            b"quota",
            b"--pool",
            pool_name,
            b"-v",
            str(qspath),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        assert proc.stdout is not None
        try:
            while True:
                try:
                    line = await proc.stdout.readuntil(b"\0")
                    line = line.rstrip(b"\0")
                except asyncio.IncompleteReadError:
                    break
                words = line.split()
                target_dir = Path(words[0].decode())
                if target_dir == qspath:
                    return QuotaUsage(used_bytes=int(words[1]), limit_bytes=int(words[3]))
            return None
        finally:
            await proc.wait()

    async def update_quota_scope(
        self,
        quota_scope_id: QuotaScopeID,
        config: QuotaConfig,
    ) -> None:
        await self._set_quota_by_pool(quota_scope_id, config.limit_bytes)

    async def unset_quota(self, quota_scope_id: QuotaScopeID) -> None:
        await self._set_quota_by_pool(quota_scope_id, 0)


# class EXAScalerFSOpModel(BaseFSOpModel):
#     pass


class EXAScalerFSVolume(BaseVolume):
    name = "exascaler"

    async def create_quota_model(self) -> AbstractQuotaModel:
        return EXAScalerQuotaModel(self.mount_path, self.local_config)

    # async def create_fsop_model(self) -> AbstractFSOpModel:
    #     return EXAScalerFSOpModel(
    #         self.mount_path,
    #         self.local_config["storage-proxy"]["scandir-limit"],
    #     )

    async def get_capabilities(self) -> FrozenSet[str]:
        return frozenset([CAP_VFOLDER, CAP_QUOTA])
