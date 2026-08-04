from __future__ import annotations

import enum
from typing import Final


class RunnerVerb(enum.StrEnum):
    CLEAN = "clean"
    BUILD = "build"
    EXEC = "exec"
    CODE = "code"
    INPUT = "input"
    EVENT = "event"
    INTERRUPT = "interrupt"
    STATUS = "status"
    COMPLETE = "complete"
    START_MODEL_SERVICE = "start-model-service"
    START_SERVICE = "start-service"
    SHUTDOWN_SERVICE = "shutdown-service"
    GET_APPS = "get-apps"
    LIST_FILES = "list-files"
    UPLOAD_FILE = "upload-file"
    DOWNLOAD_FILE = "download-file"
    DOWNLOAD_SINGLE = "download-single"
    GET_LOGS = "get-logs"

    @property
    def frame(self) -> bytes:
        return self.value.encode("ascii")


class RunnerReply(enum.StrEnum):
    STATUS = "status"
    COMPLETION = "completion"
    SERVICE_RESULT = "service-result"
    MODEL_SERVICE_RESULT = "model-service-result"
    MODEL_SERVICE_STATUS = "model-service-status"
    APPS_RESULT = "apps-result"
    FILES_RESULT = "files-result"
    TRANSFER_RESULT = "transfer-result"
    LOGS_RESULT = "logs-result"
    STDOUT = "stdout"
    STDERR = "stderr"
    MEDIA = "media"
    HTML = "html"
    LOG = "log"
    FINISHED = "finished"
    CLEAN_FINISHED = "clean-finished"
    BUILD_FINISHED = "build-finished"
    WAITING_INPUT = "waiting-input"

    @property
    def frame(self) -> bytes:
        return self.value.encode("ascii")


PLAINTEXT_BEARING: Final = frozenset({
    RunnerVerb.CLEAN,
    RunnerVerb.BUILD,
    RunnerVerb.EXEC,
    RunnerVerb.CODE,
    RunnerVerb.INPUT,
    RunnerVerb.INTERRUPT,
    RunnerVerb.COMPLETE,
    RunnerVerb.LIST_FILES,
    RunnerVerb.UPLOAD_FILE,
    RunnerVerb.DOWNLOAD_FILE,
    RunnerVerb.DOWNLOAD_SINGLE,
    RunnerVerb.GET_LOGS,
})

SERVICE_CONTROL: Final = frozenset({
    RunnerVerb.EVENT,
    RunnerVerb.STATUS,
    RunnerVerb.START_MODEL_SERVICE,
    RunnerVerb.START_SERVICE,
    RunnerVerb.SHUTDOWN_SERVICE,
    RunnerVerb.GET_APPS,
})

IN_GUEST_FILE_VERBS: Final = frozenset({
    RunnerVerb.LIST_FILES,
    RunnerVerb.UPLOAD_FILE,
    RunnerVerb.DOWNLOAD_FILE,
    RunnerVerb.DOWNLOAD_SINGLE,
    RunnerVerb.GET_LOGS,
})

CHANNEL_PROTOCOL_VERSION: Final = "bai-cc-channel/1"
