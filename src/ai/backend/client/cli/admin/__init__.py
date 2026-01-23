from ai.backend.cli.main import main


@main.group()
def admin():
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
    resource,
    resource_policy,
    scaling_group,
    session,
    storage,
    user,
    vfolder,
    quota_scope,
)
