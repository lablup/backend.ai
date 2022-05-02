import json
import sys

import click

from . import admin
from ..pretty import print_pretty, print_error, print_fail
from ...session import Session


@admin.group()
def etcd() -> None:
    """
    etcd query and manipulation commands.
    (admin privilege required)
    """


@etcd.command()
@click.argument('key', type=str, metavar='KEY')
@click.option('-p', '--prefix', is_flag=True, default=False,
              help='Get all keys prefixed with the given key.')
def get(key, prefix):
    """
    Get a ETCD value(s).

    KEY: Name of ETCD key.
    """
    with Session() as session:
        try:
            data = session.EtcdConfig.get(key, prefix)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        data = json.dumps(data, indent=2) if data else 'null'
        print_pretty(data)


@etcd.command()
@click.argument('key', type=str, metavar='KEY')
@click.argument('value', type=str, metavar='VALUE')
def set(key, value):
    """
    Set new key and value on ETCD.

    KEY: Name of ETCD key.
    VALUE: Value to set.
    """
    with Session() as session:
        try:
            value = json.loads(value)
            print_pretty('Value converted to a dictionary.')
        except json.JSONDecodeError:
            pass
        try:
            data = session.EtcdConfig.set(key, value)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if data.get('result', False) != 'ok':
            print_fail('Unable to set key/value.')
        else:
            print_pretty('Successfully set key/value.')


@etcd.command()
@click.argument('key', type=str, metavar='KEY')
@click.option('-p', '--prefix', is_flag=True, default=False,
              help='Delete all keys prefixed with the given key.')
def delete(key, prefix):
    """
    Delete key(s) from ETCD.

    KEY: Name of ETCD key.
    """
    with Session() as session:
        try:
            data = session.EtcdConfig.delete(key, prefix)
        except Exception as e:
            print_error(e)
            sys.exit(1)
        if data.get('result', False) != 'ok':
            print_fail('Unable to delete key/value.')
        else:
            print_pretty('Successfully deleted key/value.')
