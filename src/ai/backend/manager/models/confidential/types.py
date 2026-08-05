from __future__ import annotations

import enum


class ReferenceValueState(enum.StrEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


class DecisionActor(enum.StrEnum):
    MANAGER = "manager"
    GUEST = "guest"
    CLIENT = "client"


class DecisionVerdict(enum.StrEnum):
    ALLOWED = "allowed"
    DENIED = "denied"
    UNREACHABLE = "unreachable"
    OUT_OF_SCOPE = "out-of-scope"


class SessionResourceKind(enum.StrEnum):
    SESSION_CONFIG = "session-config"
    SESSION_SECRETS = "session-secrets"
    NONCE_BINDING = "nonce-binding"
    MOUNT_PLAN = "mount-plan"
    FOLDER_KEY = "folder-key"
    TUNNEL_KEY = "tunnel-key"
    PEER_DIRECTORY = "peer-directory"
    CHANNEL_KEY = "channel-key"
