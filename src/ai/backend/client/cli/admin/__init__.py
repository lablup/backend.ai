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
    group,
    image,
    keypair,
    license,
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
