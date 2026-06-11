"""raise the deployment rollout timeout default and split action retries

Reworks the deployment ``handler_options`` default so a rollout that
cannot reach STABLE eventually times out and rolls back (previously the
``default`` slot had ``timeout=null`` so the PROVISIONED wait never
expired). New default policy, mirroring
``manager.data.deployment.types.DeploymentHandlerOptions``:

  * ``default``: ``{timeout: 7200, max_retry_count: null}`` — a generous
    2h wall-clock budget covering hour-scale model-service startup
    (rolling updates fan out in batches), with no retry-count limit so
    the long PROVISIONED/DRAINING waits expire on time, not on count.
  * ``by_handler``: the deploying action sub-steps
    (``deploying-initializing`` / ``-provisioning`` / ``-promoting`` /
    ``-finalizing`` / ``-rolling-back``) carry ``max_retry_count=5`` so a
    genuinely broken deploy gives up after five attempts instead of
    churning for the full 2h.

Rewrites both stored snapshots and their column DEFAULTs:

  * ``scaling_groups.default_deployment_options`` (source for new deploys)
  * ``endpoints.options`` (existing per-deployment snapshots)

Only rows whose ``handler_options.default.timeout`` is still ``null``
(the prior auto-default — operator-set fixed timeouts are preserved) are
rewritten. That gate also makes the upgrade idempotent: a re-run finds
``timeout=7200`` and skips. Downgrade restores the prior shape on rows
carrying the new ``deploying-initializing`` key.

Revision ID: e1f7a3c9d524
Revises: 5e5d1672ccc2
Create Date: 2026-06-09

"""

# Part of: 26.6.0

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e1f7a3c9d524"
down_revision = "5e5d1672ccc2"
branch_labels = None
depends_on = None


# New DeploymentOptions DEFAULT — keep in sync with
# manager.data.deployment.types.DeploymentHandlerOptions defaults.
_NEW_DEPLOYMENT_OPTIONS_JSON = (
    "{"
    '"handler_options":{'
    '"default":{"timeout":7200,"max_retry_count":null},'
    '"by_handler":{'
    '"deploying-initializing":{"timeout":null,"max_retry_count":5},'
    '"deploying-provisioning":{"timeout":null,"max_retry_count":5},'
    '"deploying-promoting":{"timeout":null,"max_retry_count":5},'
    '"deploying-finalizing":{"timeout":null,"max_retry_count":5},'
    '"deploying-rolling-back":{"timeout":null,"max_retry_count":5}'
    "}"
    "}"
    "}"
)

# Prior DEFAULT (from fc249eccd0b2) — restored on downgrade.
_OLD_DEPLOYMENT_OPTIONS_JSON = (
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

_TARGETS: list[tuple[str, str]] = [
    ("scaling_groups", "default_deployment_options"),
    ("endpoints", "options"),
]


def _set_default(table: str, column: str, default_json: str) -> None:
    # ALTER ... SET DEFAULT takes no bind params and SQLAlchemy scans the
    # rendered SQL for ``:name`` placeholders even inside quoted literals,
    # so every ``:`` is escaped to emit a literal colon.
    escaped_json = default_json.replace(":", r"\:")
    op.execute(
        sa.text(
            f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT '{escaped_json}'\\:\\:jsonb"
        )
    )


def upgrade() -> None:
    for table, column in _TARGETS:
        op.execute(
            sa.text(
                f"""
                UPDATE {table}
                SET {column} = jsonb_set(
                    {column},
                    '{{handler_options}}',
                    (:new_options)\\:\\:jsonb -> 'handler_options'
                )
                WHERE ({column} -> 'handler_options' -> 'default' ->> 'timeout') IS NULL
                """
            ).bindparams(new_options=_NEW_DEPLOYMENT_OPTIONS_JSON)
        )
        _set_default(table, column, _NEW_DEPLOYMENT_OPTIONS_JSON)


def downgrade() -> None:
    for table, column in _TARGETS:
        op.execute(
            sa.text(
                f"""
                UPDATE {table}
                SET {column} = jsonb_set(
                    {column},
                    '{{handler_options}}',
                    (:old_options)\\:\\:jsonb -> 'handler_options'
                )
                WHERE {column} -> 'handler_options' -> 'by_handler' ? 'deploying-initializing'
                """
            ).bindparams(old_options=_OLD_DEPLOYMENT_OPTIONS_JSON)
        )
        _set_default(table, column, _OLD_DEPLOYMENT_OPTIONS_JSON)
