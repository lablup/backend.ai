"""rename ``timeouts`` JSONB key to ``handler_options``

Following the data-layer rename ``SessionTimeouts`` /
``DeploymentTimeouts`` → ``SessionHandlerOptions`` /
``DeploymentHandlerOptions`` (carrying ``HandlerOptions{timeout,
max_retry_count}`` entries instead of bare ``int | null`` values),
this migration rewrites the existing JSONB columns:

  * ``scaling_groups.default_session_options``
  * ``scaling_groups.default_deployment_options``
  * ``sessions.options``
  * ``endpoints.options``

The transformation drops the ``timeouts`` key and adds an
``handler_options`` key. ``timeouts.default: int|null`` is wrapped
into ``handler_options.default: {timeout: int|null, max_retry_count:
null}``; each ``timeouts.by_handler[k]: int|null`` becomes
``handler_options.by_handler[k]: {timeout: int|null, max_retry_count:
null}``. ``max_retry_count`` is initialised to ``null`` everywhere —
existing deployments had no per-handler retry budget, and ``null``
preserves "no retry limit" under the new
:meth:`HandlerOptions.is_retry_exhausted` semantics.

Column ``DEFAULT`` clauses are also re-written to the new shape so
fresh inserts go in with the correct schema.

Both upgrade and downgrade are idempotent: each ``UPDATE`` is gated
on the source key still being present, so re-running the same
direction is a no-op. Downgrade discards the per-handler
``max_retry_count`` (acceptable: it carried no data here).

Revision ID: fc249eccd0b2
Revises: 6b8149885649
Create Date: 2026-05-08

"""

# Part of: 26.5.0

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fc249eccd0b2"
down_revision = "6b8149885649"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Column DEFAULT payloads (post-rewrite shape).
# Mirrors ``DefaultSessionOptions().model_dump_json()`` and the equivalent
# stored views — keep in sync with manager.data.session.options /
# manager.data.deployment.types if those defaults change.
# ---------------------------------------------------------------------------

# scaling_groups.default_session_options — full DefaultSessionOptions snapshot.
# ``max_retry_count: 5`` on the ``default`` slot mirrors the legacy
# ``SERVICE_MAX_RETRIES`` threshold so coordinator give-up keeps firing
# without operator opt-in. Per-handler overrides in ``by_handler``
# leave ``max_retry_count`` as ``null`` to fall back to the default.
_DEFAULT_SESSION_OPTIONS_JSON = (
    "{"
    '"priority":10,'
    '"is_preemptible":true,'
    '"cluster_mode":"single-node",'
    '"default_failure_policy":"strict",'
    '"default_kernel_execution_spec":null,'
    '"handler_options":{'
    '"default":{"timeout":null,"max_retry_count":5},'
    '"by_handler":{}'
    "},"
    '"agent_selection_policy":"preferred"'
    "}"
)

# sessions.options — frozen SessionStoredOptions snapshot.
_SESSION_STORED_OPTIONS_JSON = (
    "{"
    '"kernel_groups":[],'
    '"handler_options":{'
    '"default":{"timeout":null,"max_retry_count":5},'
    '"by_handler":{}'
    "},"
    '"agent_selection_policy":"preferred"'
    "}"
)

# scaling_groups.default_deployment_options / endpoints.options —
# DeploymentOptions snapshot. Preserves the legacy 3600s lifecycle
# timeouts baked into ``b1a2c3d4e5f6``. ``max_retry_count=5`` flows
# through every entry so the JSONB matches what a freshly-constructed
# ``HandlerOptions()`` would emit.
_DEPLOYMENT_OPTIONS_JSON = (
    "{"
    '"handler_options":{'
    '"default":{"timeout":null,"max_retry_count":5},'
    '"by_handler":{'
    '"deploying-provisioning":{"timeout":3600,"max_retry_count":5},'
    '"deploying-rolling-back":{"timeout":3600,"max_retry_count":5},'
    '"scaling-deployments":{"timeout":3600,"max_retry_count":5}'
    "}"
    "}"
    "}"
)


# Old DEFAULT payloads — used by downgrade to restore the prior shape.
_OLD_DEFAULT_SESSION_OPTIONS_JSON = (
    "{"
    '"priority":10,'
    '"is_preemptible":true,'
    '"cluster_mode":"single-node",'
    '"default_failure_policy":"strict",'
    '"default_kernel_execution_spec":null,'
    '"timeouts":{"default":null,"by_handler":{}},'
    '"agent_selection_policy":"preferred"'
    "}"
)

_OLD_SESSION_STORED_OPTIONS_JSON = (
    "{"
    '"kernel_groups":[],'
    '"timeouts":{"default":null,"by_handler":{}},'
    '"agent_selection_policy":"preferred"'
    "}"
)

_OLD_DEPLOYMENT_OPTIONS_JSON = (
    '{"timeouts":{"default":null,"by_handler":'
    '{"deploying-provisioning":3600,'
    '"deploying-rolling-back":3600,'
    '"scaling-deployments":3600}}}'
)


# Table → (column, new_default_json, old_default_json) tuples.
_TARGETS: list[tuple[str, str, str, str]] = [
    (
        "scaling_groups",
        "default_session_options",
        _DEFAULT_SESSION_OPTIONS_JSON,
        _OLD_DEFAULT_SESSION_OPTIONS_JSON,
    ),
    ("sessions", "options", _SESSION_STORED_OPTIONS_JSON, _OLD_SESSION_STORED_OPTIONS_JSON),
    (
        "scaling_groups",
        "default_deployment_options",
        _DEPLOYMENT_OPTIONS_JSON,
        _OLD_DEPLOYMENT_OPTIONS_JSON,
    ),
    ("endpoints", "options", _DEPLOYMENT_OPTIONS_JSON, _OLD_DEPLOYMENT_OPTIONS_JSON),
]


def _set_default(table: str, column: str, default_json: str) -> None:
    """Re-write the column DEFAULT to ``default_json``.

    ``ALTER TABLE ... SET DEFAULT`` cannot accept bind parameters and
    SQLAlchemy's ``text()`` scans the rendered SQL for ``:name``
    placeholders even inside quoted literals — every ``:`` is escaped
    with ``\\:`` so SQLAlchemy emits a literal colon.
    """
    escaped_json = default_json.replace(":", r"\:")
    op.execute(
        sa.text(
            f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT '{escaped_json}'\\:\\:jsonb"
        )
    )


def _upgrade_one(table: str, column: str) -> None:
    """Rewrite the ``timeouts`` key in one JSONB column.

    Backfill convention: every produced ``HandlerOptions`` entry
    (``default`` and each ``by_handler[k]``) carries
    ``max_retry_count = 5`` — matching the new ``HandlerOptions``
    field default so existing rows look identical to what a
    freshly-constructed ``HandlerOptions()`` emits, and the
    coordinator's give-up threshold stays at the legacy 5-attempt
    budget without operator opt-in.

    Idempotent: the WHERE clause skips rows that no longer have a
    ``timeouts`` key (already migrated).
    """
    op.execute(
        sa.text(
            f"""
            UPDATE {table}
            SET {column} = (
                ({column} - 'timeouts')
                || jsonb_build_object(
                    'handler_options',
                    jsonb_build_object(
                        'default',
                        jsonb_build_object(
                            'timeout', {column}->'timeouts'->'default',
                            'max_retry_count', 5
                        ),
                        'by_handler',
                        COALESCE(
                            (
                                SELECT jsonb_object_agg(
                                    k,
                                    jsonb_build_object(
                                        'timeout', v,
                                        'max_retry_count', 5
                                    )
                                )
                                FROM jsonb_each({column}->'timeouts'->'by_handler') AS x(k, v)
                            ),
                            '{{}}'::jsonb
                        )
                    )
                )
            )
            WHERE {column} ? 'timeouts'
            """
        )
    )


def _downgrade_one(table: str, column: str) -> None:
    """Reverse ``handler_options`` → ``timeouts``, dropping
    ``max_retry_count`` (no callers consumed it under the old schema).

    Idempotent: skips rows that no longer have ``handler_options``.
    """
    op.execute(
        sa.text(
            f"""
            UPDATE {table}
            SET {column} = (
                ({column} - 'handler_options')
                || jsonb_build_object(
                    'timeouts',
                    jsonb_build_object(
                        'default',
                        {column}->'handler_options'->'default'->'timeout',
                        'by_handler',
                        COALESCE(
                            (
                                SELECT jsonb_object_agg(k, v->'timeout')
                                FROM jsonb_each({column}->'handler_options'->'by_handler')
                                    AS x(k, v)
                            ),
                            '{{}}'::jsonb
                        )
                    )
                )
            )
            WHERE {column} ? 'handler_options'
            """
        )
    )


def upgrade() -> None:
    for table, column, new_default, _old in _TARGETS:
        _upgrade_one(table, column)
        _set_default(table, column, new_default)


def downgrade() -> None:
    for table, column, _new, old_default in _TARGETS:
        _downgrade_one(table, column)
        _set_default(table, column, old_default)
