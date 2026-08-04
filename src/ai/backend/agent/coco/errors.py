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


class HostFileTransferRefused(_CocoRefusal):
    error_type = _PREFIX + "host-file-transfer-refused"
    error_title = "Host-side file transfer is dead: it becomes an in-guest verb over the channel."


class HostLogReadRefused(_CocoRefusal):
    error_type = _PREFIX + "host-log-read-refused"
    error_title = "Host-side guest console reads are denied by the guest agent policy."


class HostConfigReadbackRefused(_CocoRefusal):
    error_type = _PREFIX + "host-config-readback-refused"
    error_title = "Restart state comes from the manager and a fresh fetch, never from host disk."


class MultiNodeSessionRefused(_CocoRefusal):
    error_type = _PREFIX + "multi-node-session-refused"
    error_title = "Multi-node sessions are refused: inter-node bytes would cross the underlay bare."


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
