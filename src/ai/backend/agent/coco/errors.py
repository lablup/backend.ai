from typing import override

from aiohttp import web

from ai.backend.common.exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)

_PREFIX = "https://api.backend.ai/probs/agent/coco/"


class _CocoFailure(BackendAIError, web.HTTPInternalServerError):
    _domain = ErrorDomain.KERNEL
    _operation = ErrorOperation.CREATE
    _detail = ErrorDetail.INTERNAL_ERROR

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(domain=self._domain, operation=self._operation, error_detail=self._detail)


class _CocoRefusal(BackendAIError, web.HTTPNotImplemented):
    _domain = ErrorDomain.KERNEL
    _operation = ErrorOperation.GENERIC
    _detail = ErrorDetail.NOT_IMPLEMENTED

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(domain=self._domain, operation=self._operation, error_detail=self._detail)


class SessionCommitRefused(_CocoRefusal):
    error_type = _PREFIX + "session-commit-refused"
    error_title = "Session commit is dead: image layers unpack in the guest, never on the host."


class LaunchOptionRefused(_CocoRefusal):
    error_type = _PREFIX + "launch-option-refused"
    error_title = "Resource options the confidential runtime does not act on are refused, never dropped."


class HostFileTransferRefused(_CocoRefusal):
    error_type = _PREFIX + "host-file-transfer-refused"
    error_title = "Host-side file transfer is dead: it becomes an in-guest verb over the channel."


class HostLogReadRefused(_CocoRefusal):
    error_type = _PREFIX + "host-log-read-refused"
    error_title = "Host-side guest console reads are denied by the guest agent policy."


class HostConfigReadbackRefused(_CocoRefusal):
    error_type = _PREFIX + "host-config-readback-refused"
    error_title = "Restart state comes from the manager and a fresh fetch, never from host disk."


class ImagePushRefused(_CocoRefusal):
    error_type = _PREFIX + "image-push-refused"
    error_title = "Image push from the host is unavailable under the confidential runtime."


class FractionalAcceleratorRefused(_CocoFailure, web.HTTPBadRequest):
    error_type = _PREFIX + "fractional-accelerator-refused"
    error_title = "Fractional accelerators are refused: whole-device passthrough only."
    _detail = ErrorDetail.INVALID_PARAMETERS


class AcceleratorHooksRefused(_CocoFailure):
    error_type = _PREFIX + "accelerator-hooks-refused"
    error_title = "A plugin returned hooks; the confidential path injects nothing from the host."
    _detail = ErrorDetail.INVALID_PARAMETERS


class ImageDistroUnresolved(_CocoFailure, web.HTTPBadRequest):
    error_type = _PREFIX + "image-distro-unresolved"
    error_title = "The image's base distribution is not in its labels and the host may not run it."
    _detail = ErrorDetail.INVALID_DATA_FORMAT


class ImageDigestUnresolved(_CocoFailure, web.HTTPBadRequest):
    error_type = _PREFIX + "image-digest-unresolved"
    error_title = "No image manifest digest was supplied; the measured blob is keyed by it."
    _detail = ErrorDetail.INVALID_DATA_FORMAT


class MeasuredBlobUnavailable(_CocoFailure):
    error_type = _PREFIX + "measured-blob-unavailable"
    error_title = "No measured configuration blob is registered for this image digest."
    _detail = ErrorDetail.NOT_FOUND


class MeasuredBlobCorrupted(_CocoFailure):
    error_type = _PREFIX + "measured-blob-corrupted"
    error_title = (
        "The measured blob does not match its content address; attaching it would deny all."
    )
    _detail = ErrorDetail.INVALID_DATA_FORMAT


class BrokerUnreachableFromNamespace(_CocoFailure):
    error_type = _PREFIX + "broker-unreachable-from-namespace"
    error_title = (
        "The key broker's authorisation shim is not reachable from the session network"
        " namespace. A guest launched now would boot, attest, fail to fetch and starve,"
        " which is indistinguishable from a genuine tamper detection."
    )
    _detail = ErrorDetail.UNREACHABLE


class NetworkSetupFailed(_CocoFailure):
    error_type = _PREFIX + "network-setup-failed"
    error_title = "Session network namespace construction failed."


class ReleaseNotConfirmed(_CocoFailure):
    error_type = _PREFIX + "release-not-confirmed"
    error_title = "The guest never opened its runner channel, so its secret fetch is unconfirmed."
    _detail = ErrorDetail.NOT_READY


class RuntimeInvocationFailed(_CocoFailure):
    error_type = _PREFIX + "runtime-invocation-failed"
    error_title = "The container runtime client failed."


class VfioDeviceUnavailable(_CocoFailure):
    error_type = _PREFIX + "vfio-device-unavailable"
    error_title = "An allocated accelerator has no vfio character device bound at launch time."
    _detail = ErrorDetail.UNAVAILABLE


class StorageBindRefused(_CocoRefusal):
    error_type = _PREFIX + "storage-bind-refused"
    error_title = (
        "The confidential path emits no storage bind mount on the host side. Folders reach the"
        " guest as an attested mount plan the guest mounts and decrypts for itself."
    )


class UnmanagedFolderRefused(_CocoRefusal):
    error_type = _PREFIX + "unmanaged-folder-refused"
    error_title = "Unmanaged folders bind an arbitrary host path and skip the storage service."


class HostLogFolderRefused(_CocoRefusal):
    error_type = _PREFIX + "host-log-folder-refused"
    error_title = (
        "The log folder's host bind is gone: it would carry enclave plaintext to the host."
    )


class FolderEncryptionMissing(_CocoFailure, web.HTTPBadRequest):
    error_type = _PREFIX + "folder-encryption-missing"
    error_title = (
        "A folder reached a confidential kernel without an encryption descriptor, or with an"
        " empty key reference. Mounting it would degrade silently to plaintext."
    )
    _detail = ErrorDetail.INVALID_PARAMETERS


class MountPlanMissing(_CocoFailure, web.HTTPBadRequest):
    error_type = _PREFIX + "mount-plan-missing"
    error_title = "Folders were granted but the manager provisioned no mount plan resource."
    _detail = ErrorDetail.INVALID_PARAMETERS


class BlockVolumeUnavailable(_CocoFailure):
    error_type = _PREFIX + "block-volume-unavailable"
    error_title = (
        "A per-guest block volume could not be provisioned. Scratch and the image store are"
        " opaque devices the guest keys itself; there is no host-side fallback."
    )
    _detail = ErrorDetail.UNAVAILABLE


class RelayUnavailable(_CocoFailure):
    error_type = _PREFIX + "relay-unavailable"
    error_title = "The blind byte relay cannot run on this kernel."
    _detail = ErrorDetail.UNAVAILABLE


class RawCircuitRefused(_CocoRefusal):
    error_type = _PREFIX + "raw-circuit-refused"
    error_title = "Raw circuits are refused outside the self-encrypting allowlist."


class ChannelKeyOnHostRefused(_CocoFailure):
    error_type = _PREFIX + "channel-key-on-host-refused"
    error_title = "The session channel key may never be present on the agent host."
    _detail = ErrorDetail.FORBIDDEN


class ChannelTerminatedVerbRefused(_CocoRefusal):
    error_type = _PREFIX + "channel-terminated-verb-refused"
    error_title = "This verb moved off the agent onto the end-to-end guest channel."


class HostPrivilegeWriteRefused(_CocoRefusal):
    error_type = _PREFIX + "host-privilege-write-refused"
    error_title = "The host does not write root into the tenant's container."
