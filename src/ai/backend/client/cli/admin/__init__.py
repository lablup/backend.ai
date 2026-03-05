from ai.backend.cli.main import main


@main.group()
def admin() -> None:
    """
    Administrative command set
    """


from . import (  # noqa
    acl,
    agent,
    domain,
    etcd,
    export,
    group,
    image,
    keypair,
    license,  # noqa: A004
    manager,
    prometheus_query_preset,
    resource,
    resource_policy,
    scaling_group,
    session,
    storage,
    user,
    vfolder,
    quota_scope,
)
