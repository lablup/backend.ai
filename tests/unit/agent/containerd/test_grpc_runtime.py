import gzip
import hashlib
import json
import signal
import tarfile
from types import SimpleNamespace
from typing import Any, cast

from ai.backend.agent.containerd.runtime.grpc import ContainerdGrpcRuntime, _chain_id


class TestChainId:
    def test_single_layer_is_the_diff_id(self) -> None:
        assert _chain_id(["sha256:aaa"]) == "sha256:aaa"

    def test_empty_is_empty(self) -> None:
        assert _chain_id([]) == ""

    def test_two_layers_fold_with_sha256(self) -> None:
        d0, d1 = "sha256:aaa", "sha256:bbb"
        expected = "sha256:" + hashlib.sha256(f"{d0} {d1}".encode()).hexdigest()
        assert _chain_id([d0, d1]) == expected

    def test_three_layers_fold_left(self) -> None:
        d = ["sha256:a", "sha256:b", "sha256:c"]
        c1 = "sha256:" + hashlib.sha256(b"sha256:a sha256:b").hexdigest()
        c2 = "sha256:" + hashlib.sha256(f"{c1} sha256:c".encode()).hexdigest()
        assert _chain_id(d) == c2

    def test_deterministic(self) -> None:
        d = ["sha256:1", "sha256:2", "sha256:3"]
        assert _chain_id(d) == _chain_id(d)


class TestListContainerInfos:
    def _runtime(self, task_status: str | None) -> Any:
        # cast to Any: we are swapping in fakes for the gRPC stubs, which are not subtypes of the
        # generated stub classes.
        rt = cast(Any, ContainerdGrpcRuntime.__new__(ContainerdGrpcRuntime))

        class _Stub:
            async def List(self, req: Any, metadata: Any = None) -> Any:
                container = SimpleNamespace(id="c1", image="img:1", labels={"k": "v"})
                return SimpleNamespace(containers=[container])

        async def container_status(container_id: str) -> str | None:
            return task_status

        rt._containers_stub = lambda: _Stub()
        rt.container_status = container_status
        type(rt)._md = property(lambda self: [])
        return rt

    async def test_container_without_a_task_reports_created(self) -> None:
        # No task => Containers.Create has returned but Tasks.Create has not: the kernel is still
        # being created. Reporting "stopped" here made the agent map it to EXITED, and the
        # lifecycle sync then cleaned a kernel that was mid-creation.
        rt = self._runtime(None)
        infos = await rt.list_container_infos()
        assert infos[0].status == "created"

    async def test_task_status_is_passed_through(self) -> None:
        rt = self._runtime("running")
        infos = await rt.list_container_infos()
        assert infos[0].status == "running"


class TestStopContainer:
    """Graceful stop: SIGTERM, wait for exit, then SIGKILL — Docker's container.stop() parity."""

    def _runtime(self, statuses: list[str | None]) -> tuple[Any, list[int]]:
        rt = ContainerdGrpcRuntime.__new__(ContainerdGrpcRuntime)
        signals: list[int] = []
        self.broadcasts: list[bool] = []
        seq = iter(statuses)

        async def kill_container(
            container_id: str, *, signal: int, all_processes: bool = True
        ) -> None:
            signals.append(signal)
            self.broadcasts.append(all_processes)

        async def container_status(container_id: str) -> str | None:
            return next(seq, "stopped")

        rt.kill_container = kill_container  # type: ignore[method-assign]
        rt.container_status = container_status  # type: ignore[method-assign]
        return rt, signals

    async def test_graceful_signal_is_sigint(self) -> None:
        # Docker's StopSignal for kernels. (The runner traps SIGTERM too, so this is parity with
        # Docker rather than a behavioural fix on its own.)
        rt, signals = self._runtime(["running", "stopped"])
        await rt.stop_container("c1", grace_period=1.0)
        assert signals == [signal.SIGINT]

    async def test_the_graceful_signal_goes_to_pid_1_only(self) -> None:
        # Broadcasting the stop signal to every process (all=True) tears the user's workload down
        # underneath the kernel runner, instead of letting the runner shut its children down in
        # order — which is the entire point of the grace period. Docker signals PID 1 only.
        rt, _signals = self._runtime(["running", "stopped"])
        await rt.stop_container("c1", grace_period=1.0)
        assert self.broadcasts == [False]

    async def test_the_final_sigkill_is_broadcast(self) -> None:
        # Once the grace period is up, nothing may survive: SIGKILL every process.
        rt, signals = self._runtime(["running", "running", "running"])
        await rt.stop_container("c1", grace_period=0.15)
        assert signals == [signal.SIGINT, signal.SIGKILL]
        assert self.broadcasts == [False, True]

    async def test_sigkill_when_grace_expires(self) -> None:
        # the task never exits within the grace window -> graceful signal, then SIGKILL
        rt, signals = self._runtime(["running", "running", "running"])
        await rt.stop_container("c1", grace_period=0.15)  # ~1 poll tick
        assert signals == [signal.SIGINT, signal.SIGKILL]

    async def test_already_gone_is_a_noop_after_the_graceful_signal(self) -> None:
        rt, signals = self._runtime([None])
        await rt.stop_container("c1", grace_period=1.0)
        assert signals == [signal.SIGINT]  # sent (swallows NOT_FOUND), no SIGKILL


class TestExportImage:
    """The session-export flow's downloadable artifact.

    This used to be a `log.warning(...not yet implemented)`: the commit reported success and no
    file was ever written.
    """

    def _runtime(self, tmp_path: Any) -> Any:
        rt = ContainerdGrpcRuntime.__new__(ContainerdGrpcRuntime)
        config = b'{"rootfs": {"diff_ids": ["sha256:aaa"]}}'
        layer = b"layer-bytes"
        config_digest = "sha256:" + hashlib.sha256(config).hexdigest()
        layer_digest = "sha256:" + hashlib.sha256(layer).hexdigest()
        manifest = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "config": {"digest": config_digest, "size": len(config)},
            "layers": [{"digest": layer_digest, "size": len(layer)}],
        }
        blobs = {config_digest: config, layer_digest: layer}

        async def _resolve_manifest(image_ref: str) -> Any:
            return manifest

        async def _read_content(digest: str) -> bytes:
            return blobs[digest]

        rt._resolve_manifest = _resolve_manifest  # type: ignore[method-assign]
        rt._read_content = _read_content  # type: ignore[method-assign]
        return rt, manifest, blobs

    async def test_writes_a_gzipped_oci_layout(self, tmp_path: Any) -> None:
        rt, manifest, blobs = self._runtime(tmp_path)
        dest = tmp_path / "out" / "export.tar.gz"
        await rt.export_image("img:1", dest)

        assert dest.is_file()
        with gzip.open(dest, "rb") as gz, tarfile.open(fileobj=gz, mode="r|") as tar:
            names = [m.name for m in tar]
        # a valid OCI image layout: the marker, the index, and every blob
        assert "oci-layout" in names
        assert "index.json" in names
        for digest in blobs:
            algo, _, hexd = digest.partition(":")
            assert f"blobs/{algo}/{hexd}" in names

    async def test_index_points_at_the_manifest_blob(self, tmp_path: Any) -> None:
        rt, _manifest, _blobs = self._runtime(tmp_path)
        dest = tmp_path / "export.tar.gz"
        await rt.export_image("img:1", dest)

        with gzip.open(dest, "rb") as gz, tarfile.open(fileobj=gz, mode="r|") as tar:
            members = {m.name: tar.extractfile(m).read() for m in tar if m.isfile()}  # type: ignore[union-attr]
        index = json.loads(members["index.json"])
        descriptor = index["manifests"][0]
        algo, _, hexd = descriptor["digest"].partition(":")
        manifest_blob = members[f"blobs/{algo}/{hexd}"]
        # the descriptor must actually describe the blob it points at
        assert descriptor["size"] == len(manifest_blob)
        assert hexd == hashlib.sha256(manifest_blob).hexdigest()
        assert descriptor["annotations"]["org.opencontainers.image.ref.name"] == "img:1"
