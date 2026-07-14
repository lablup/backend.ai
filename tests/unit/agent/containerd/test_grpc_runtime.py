import base64
import gzip
import hashlib
import json
import signal
import tarfile
from types import SimpleNamespace
from typing import Any, cast

import grpc
import pytest

from ai.backend.agent.containerd._grpcapi.api.types import mount_pb2
from ai.backend.agent.containerd._grpcapi.api.types.transfer import imagestore_pb2, registry_pb2
from ai.backend.agent.containerd.runtime.grpc import ContainerdGrpcRuntime, _chain_id

_ACTIVE_MOUNT = mount_pb2.Mount(type="overlay", source="overlay", options=["upperdir=/active"])
_BASE_VIEW_MOUNT = mount_pb2.Mount(type="overlay", source="overlay", options=["lowerdir=/base"])


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


class TestRemoveContainerWithAStuckTask:
    """A task wedged in D-state (a hung NFS vfolder) survives even SIGKILL, so Tasks.Delete fails
    FAILED_PRECONDITION. That must not abort the clean and leak the container, its snapshot and its
    logs — every stuck kernel would leave one behind."""

    def _runtime(self) -> tuple[Any, dict[str, bool]]:
        rt = cast(Any, ContainerdGrpcRuntime.__new__(ContainerdGrpcRuntime))
        rt._rootfs = {"c1": []}
        deleted = {"task": False, "container": False, "snapshot": False}

        async def kill_container(
            container_id: str, *, signal: int, all_processes: bool = True
        ) -> None:
            pass

        async def container_status(container_id: str) -> str | None:
            return "running"  # never dies

        class _Tasks:
            async def Delete(self, req: Any, metadata: Any = None, timeout: Any = None) -> Any:
                deleted["task"] = True
                raise grpc.aio.AioRpcError(
                    grpc.StatusCode.FAILED_PRECONDITION,
                    None,
                    None,
                    "cannot delete a running process",
                )

        class _Containers:
            async def Delete(self, req: Any, metadata: Any = None, timeout: Any = None) -> Any:
                deleted["container"] = True

        class _Snapshots:
            async def Remove(self, req: Any, metadata: Any = None, timeout: Any = None) -> Any:
                deleted["snapshot"] = True
                # the live task still has the overlay mounted, so the snapshot is "in use"
                raise grpc.aio.AioRpcError(
                    grpc.StatusCode.FAILED_PRECONDITION, None, None, "snapshot is in use"
                )

        rt.kill_container = kill_container
        rt.container_status = container_status
        rt._tasks_stub = lambda: _Tasks()
        rt._containers_stub = lambda: _Containers()
        rt._snapshots_stub = lambda: _Snapshots()
        type(rt)._md = property(lambda self: [])
        return rt, deleted

    async def test_a_task_that_will_not_die_still_gets_its_records_cleaned(self) -> None:
        rt, deleted = self._runtime()
        await rt.remove_container("c1")  # must not raise, though the snapshot is still mounted
        assert deleted == {"task": True, "container": True, "snapshot": True}  # all attempted
        assert "c1" not in rt._rootfs  # and the clean ran to completion regardless


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

        async def _read_content_chunks(digest: str) -> Any:
            # Layers are streamed a chunk at a time (never held whole in memory); emit two chunks
            # so the streaming path is actually exercised, not just a single-shot read.
            data = blobs[digest]
            yield data[: len(data) // 2]
            yield data[len(data) // 2 :]

        rt._resolve_manifest = _resolve_manifest  # type: ignore[method-assign]
        rt._read_content = _read_content  # type: ignore[method-assign]
        rt._read_content_chunks = _read_content_chunks  # type: ignore[method-assign]
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


class _CommitHarness:
    """The containerd services a commit touches, faked with the semantics the real ones have.

    Two of those semantics are the whole reason this test exists, and both were learned the hard way
    against a live daemon: the differ returns a descriptor whose annotations are EMPTY and records
    the layer's uncompressed digest as a *content label* instead; and the garbage collector reaches
    a blob only through the `containerd.io/gc.ref.*` labels of whatever references it.
    """

    BASE_LAYER = {
        "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
        "digest": "sha256:base-layer",
        "size": 768,
    }
    BASE_DIFF_ID = "sha256:base-diff-id"
    NEW_LAYER_DIGEST = "sha256:new-layer-blob"  # the compressed blob
    NEW_DIFF_ID = "sha256:new-layer-uncompressed"  # what the config must record

    def __init__(self) -> None:
        self.diff_requests: list[Any] = []
        self.views: list[Any] = []
        self.removed_snapshots: list[str] = []
        self.paused: list[str] = []
        self.resumed: list[str] = []
        self.written: dict[str, tuple[bytes, dict[str, str]]] = {}
        self.label_updates: list[tuple[str, list[str]]] = []
        self.created_images: list[Any] = []
        self.deleted_content: list[str] = []
        self.fail_image_create = False

    def runtime(self) -> Any:
        rt = cast(Any, ContainerdGrpcRuntime.__new__(ContainerdGrpcRuntime))
        harness = self

        base_config = {
            "rootfs": {"type": "layers", "diff_ids": [self.BASE_DIFF_ID]},
            "config": {"Labels": {"base": "yes"}},
            "history": [{"created_by": "base"}],
        }
        base_manifest = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "config": {"digest": "sha256:base-config", "size": 1},
            "layers": [self.BASE_LAYER],
        }

        class _Snapshots:
            async def Mounts(self, req: Any, metadata: Any = None) -> Any:
                return SimpleNamespace(mounts=[_ACTIVE_MOUNT])

            async def View(self, req: Any, metadata: Any = None) -> Any:
                harness.views.append(req)
                return SimpleNamespace(mounts=[_BASE_VIEW_MOUNT])

            async def Remove(self, req: Any, metadata: Any = None) -> Any:
                harness.removed_snapshots.append(req.key)
                return SimpleNamespace()

        class _Diff:
            async def Diff(self, req: Any, metadata: Any = None) -> Any:
                harness.diff_requests.append(req)
                # As the real differ does: no annotations on the descriptor...
                return SimpleNamespace(
                    diff=SimpleNamespace(digest=harness.NEW_LAYER_DIGEST, size=177, annotations={})
                )

        class _Content:
            async def Info(self, req: Any, metadata: Any = None) -> Any:
                # ...the diff_id lives here instead.
                return SimpleNamespace(
                    info=SimpleNamespace(labels={"containerd.io/uncompressed": harness.NEW_DIFF_ID})
                )

            async def Update(self, req: Any, metadata: Any = None) -> Any:
                harness.label_updates.append((req.info.digest, list(req.update_mask.paths)))
                return SimpleNamespace()

            async def Delete(self, req: Any, metadata: Any = None) -> Any:
                harness.deleted_content.append(req.digest)
                return SimpleNamespace()

        class _Tasks:
            async def Pause(self, req: Any, metadata: Any = None) -> Any:
                harness.paused.append(req.container_id)
                return SimpleNamespace()

            async def Resume(self, req: Any, metadata: Any = None) -> Any:
                harness.resumed.append(req.container_id)
                return SimpleNamespace()

        class _Images:
            async def Create(self, req: Any, metadata: Any = None) -> Any:
                if harness.fail_image_create:
                    raise grpc.aio.AioRpcError(grpc.StatusCode.INTERNAL, None, None, "boom")
                harness.created_images.append(req.image)
                return SimpleNamespace()

        async def _resolve_manifest(image_ref: str) -> Any:
            return base_manifest

        async def _read_content(digest: str) -> bytes:
            return json.dumps(base_config).encode()

        async def _write_content(
            data: bytes, media_type: str, *, labels: Any = None
        ) -> dict[str, Any]:
            digest = "sha256:" + hashlib.sha256(data).hexdigest()
            harness.written[digest] = (data, dict(labels or {}))
            return {"mediaType": media_type, "digest": digest, "size": len(data)}

        rt._snapshots_stub = lambda: _Snapshots()
        rt._diff_stub = lambda: _Diff()
        rt._content_stub = lambda: _Content()
        rt._tasks_stub = lambda: _Tasks()
        rt._images_stub = lambda: _Images()
        rt._resolve_manifest = _resolve_manifest
        rt._write_content = _write_content
        rt._read_content = _read_content
        type(rt)._md = property(lambda self: [])
        return rt

    def manifest(self) -> dict[str, Any]:
        for digest, (data, _labels) in self.written.items():
            payload = json.loads(data)
            if payload.get("layers") is not None:
                return cast(dict[str, Any], payload)
        raise AssertionError("no manifest was written")

    def manifest_labels(self) -> dict[str, str]:
        for digest, (data, labels) in self.written.items():
            if json.loads(data).get("layers") is not None:
                return labels
        raise AssertionError("no manifest was written")

    def config(self) -> dict[str, Any]:
        for digest, (data, _labels) in self.written.items():
            payload = json.loads(data)
            if payload.get("rootfs") is not None:
                return cast(dict[str, Any], payload)
        raise AssertionError("no config was written")


class TestCommitContainer:
    async def _commit(self) -> _CommitHarness:
        harness = _CommitHarness()
        rt = harness.runtime()
        await rt.commit_container(
            "kern-1",
            base_image_ref="base:1",
            target_ref="committed:1",
            labels={"ai.backend.customized-image.name": "mine"},
        )
        return harness

    async def test_the_layer_is_a_diff_against_the_base_not_the_whole_rootfs(self) -> None:
        # `left=[]` diffs the rootfs against nothing, flattening the entire OS into one layer that
        # shares nothing with the base image: gigabytes duplicated per commit, a push that uploads
        # the whole OS, and a pull that can reuse none of what the puller already has.
        harness = await self._commit()
        request = harness.diff_requests[0]
        assert list(request.left) == [_BASE_VIEW_MOUNT]
        assert list(request.right) == [_ACTIVE_MOUNT]

    async def test_the_base_layers_are_kept_and_ours_is_appended(self) -> None:
        harness = await self._commit()
        layers = harness.manifest()["layers"]
        assert layers[0] == harness.BASE_LAYER  # the same blob, byte for byte: stored once
        assert layers[1]["digest"] == harness.NEW_LAYER_DIGEST
        assert layers[1]["mediaType"] == "application/vnd.oci.image.layer.v1.tar+gzip"

    async def test_a_failure_after_the_diff_drops_the_gc_roots_and_deletes_the_blobs(self) -> None:
        # A GC root is never collected, even after the image is deleted, so a commit that failed
        # after writing the layer/config (here, Images.Create errors) would pin gigabytes forever.
        harness = _CommitHarness()
        harness.fail_image_create = True
        rt = harness.runtime()

        with pytest.raises(grpc.aio.AioRpcError):
            await rt.commit_container(
                "kern-1", base_image_ref="base:1", target_ref="committed:1", labels={}
            )

        # every blob the commit wrote had its gc.root label cleared...
        cleared = {
            digest
            for digest, paths in harness.label_updates
            if "labels.containerd.io/gc.root" in paths
        }
        assert harness.NEW_LAYER_DIGEST in cleared  # the layer
        assert cleared & set(harness.written)  # the config/manifest it wrote
        # ...and was deleted from the content store
        assert harness.NEW_LAYER_DIGEST in harness.deleted_content

    async def test_the_config_records_the_uncompressed_digest_as_the_diff_id(self) -> None:
        # The blob's own digest is the COMPRESSED one. Recording it produces an image containerd
        # stores happily and then refuses to unpack ("wrong diff id calculated on extraction").
        harness = await self._commit()
        diff_ids = harness.config()["rootfs"]["diff_ids"]
        assert diff_ids == [harness.BASE_DIFF_ID, harness.NEW_DIFF_ID]
        assert harness.NEW_LAYER_DIGEST not in diff_ids

    async def test_the_manifest_names_its_config_and_every_layer_for_the_gc(self) -> None:
        # containerd's GC reaches content only through these labels. Without them the config and
        # layers are unreferenced, the next GC pass deletes them, and the committed image is left an
        # empty shell: `ctr images check` says "incomplete (0/2)" and running it fails with
        # "content digest ...: not found". (Verified against a live daemon.)
        harness = await self._commit()
        labels = harness.manifest_labels()
        config_digest = harness.manifest()["config"]["digest"]
        assert labels["containerd.io/gc.ref.content.config"] == config_digest
        assert labels["containerd.io/gc.ref.content.l.0"] == harness.BASE_LAYER["digest"]
        assert labels["containerd.io/gc.ref.content.l.1"] == harness.NEW_LAYER_DIGEST

    async def test_the_blobs_are_gc_roots_until_the_image_references_them(self) -> None:
        # Between writing a blob and creating the image, nothing references it — and the GC deletes
        # what nothing references, including a 2 GB layer we are still assembling an image around.
        harness = await self._commit()
        for _digest, (_data, labels) in harness.written.items():
            assert "containerd.io/gc.root" in labels

    async def test_the_roots_are_released_once_the_image_exists(self) -> None:
        # A GC root is never collected — not even after the image is deleted. Leaving them on would
        # pin every commit's layers on the node forever.
        harness = await self._commit()
        rooted = {digest for digest, (_d, labels) in harness.written.items()}
        rooted.add(harness.NEW_LAYER_DIGEST)  # the differ's blob is rooted through the Diff labels
        dropped = {digest for digest, _paths in harness.label_updates}
        assert rooted == dropped
        for _digest, paths in harness.label_updates:
            # only that one label: the differ's `uncompressed` label on the layer is how containerd
            # maps a diff_id back to the blob, and wiping it would break the unpack.
            assert paths == ["labels.containerd.io/gc.root"]

    async def test_the_container_is_frozen_while_its_rootfs_is_read(self) -> None:
        # `docker commit` pauses by default: a rootfs read while it is being written yields a layer
        # of half-written files, and the user is not told which.
        harness = await self._commit()
        assert harness.paused == ["kern-1"]
        assert harness.resumed == ["kern-1"]

    async def test_the_base_view_is_removed(self) -> None:
        # It is a snapshot like any other; leaving one behind per commit leaks the snapshotter.
        harness = await self._commit()
        assert harness.removed_snapshots == [harness.views[0].key]

    async def test_the_image_points_at_the_manifest(self) -> None:
        harness = await self._commit()
        image = harness.created_images[0]
        manifest_digest = next(
            digest
            for digest, (data, _l) in harness.written.items()
            if json.loads(data).get("layers") is not None
        )
        assert image.name == "committed:1"
        assert image.target.digest == manifest_digest

    async def test_the_caller_labels_are_merged_into_the_config(self) -> None:
        harness = await self._commit()
        labels = harness.config()["config"]["Labels"]
        assert labels["ai.backend.customized-image.name"] == "mine"
        assert labels["base"] == "yes"  # the base image's own labels survive


class TestPullPlatform:
    """A pull fetches only THIS node's platform. An empty platforms list means "all platforms" to
    the transfer service, so a multi-arch image (Backend.AI publishes amd64 + arm64) would download
    and store every architecture's layers — ~2x pull time and disk on every agent. (Verified live:
    pulling a 7-arch image stored only the host arch's manifest + layers.)"""

    async def _pulled_destination(self) -> Any:
        rt = cast(Any, ContainerdGrpcRuntime.__new__(ContainerdGrpcRuntime))
        rt._registry_hosts_dir = None
        captured: dict[str, Any] = {}

        class _Transfer:
            async def Transfer(self, req: Any, metadata: Any = None) -> Any:
                dest = imagestore_pb2.ImageStore()
                dest.ParseFromString(req.destination.value)
                captured["dest"] = dest
                return SimpleNamespace()

        rt._transfer_stub = lambda: _Transfer()
        type(rt)._md = property(lambda self: [])
        await rt.pull_image("reg/img:1")
        return captured["dest"]

    async def test_pull_pins_the_host_platform(self) -> None:
        dest = await self._pulled_destination()
        assert len(dest.platforms) == 1  # exactly one, not "all"
        assert dest.platforms[0].os == "linux"
        assert dest.platforms[0].architecture in ("amd64", "arm64")

    async def test_the_unpack_is_pinned_to_the_same_platform(self) -> None:
        dest = await self._pulled_destination()
        assert dest.unpacks[0].platform.architecture == dest.platforms[0].architecture


class TestRegistryResolution:
    """How a registry that is not plain public HTTPS gets described.

    Docker gets this for free: dockerd applies its own daemon.json / certs.d. containerd's transfer
    service reads a registry's hosts.toml only when the CLIENT names the directory, so an agent that
    passes nothing says "every registry is public HTTPS with a well-known CA" — and a self-signed or
    plain-HTTP registry fails with `server gave HTTP response to HTTPS client` even on a host that
    has it correctly configured for ctr and nerdctl. (Verified against a live plain-HTTP registry:
    the same pull fails without the directory and succeeds with it.)
    """

    def _resolver(self, runtime: Any, auth: Any = None) -> Any:
        registry = runtime._oci_registry("reg:5000/img:1", auth)
        parsed = registry_pb2.OCIRegistry()
        parsed.ParseFromString(registry.value)
        return parsed

    def test_the_host_config_directory_is_passed_to_containerd(self) -> None:
        runtime = ContainerdGrpcRuntime(registry_hosts_dir="/etc/containerd/certs.d")
        assert self._resolver(runtime).resolver.host_dir == "/etc/containerd/certs.d"

    def test_an_unset_directory_is_not_sent_as_an_empty_path(self) -> None:
        runtime = ContainerdGrpcRuntime(registry_hosts_dir=None)
        assert self._resolver(runtime).resolver.host_dir == ""

    def test_credentials_still_travel_as_a_basic_auth_header(self) -> None:
        runtime = ContainerdGrpcRuntime(registry_hosts_dir="/etc/containerd/certs.d")
        resolver = self._resolver(runtime, {"username": "u", "password": "p"}).resolver
        expected = "Basic " + base64.b64encode(b"u:p").decode()
        assert resolver.headers["Authorization"] == expected
        assert resolver.host_dir == "/etc/containerd/certs.d"  # and both at once
