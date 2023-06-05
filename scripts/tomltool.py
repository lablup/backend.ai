"""
A simple script to get/set a specific key in a TOML file or a TOML data streamed via stdin.
"""
import argparse
import io
import re
import sys
from pathlib import Path

import tomlkit
from tomlkit.exceptions import NonExistentKey
from tomlkit.items import AbstractTable, Array


rx_index = re.compile(r"^(?P<key>\w+)(\[(?P<index>\d+)\])?$")


def do_get(args):
    filepath = args.file
    if filepath == "-":
        args.file = sys.stdin
    else:
        args.file = open(args.file, "rb")
    doc = tomlkit.load(args.file)
    keytree = args.key.split(".")
    keytree_traversed = keytree[:]
    table = doc
    try:
        while True:
            try:
                k = keytree_traversed.pop(0)
            except IndexError:
                break
            if (match_index := rx_index.search(k)) and (
                (index := match_index.group("index")) is not None
            ):
                table = table[match_index.group("key")][int(index)]
            else:
                table = table[k]
        print(table)
    except NonExistentKey as e:
        print(e.args[0], file=sys.stderr)
        sys.exit(1)
    finally:
        if isinstance(args.file, io.BufferedIOBase):
            args.file.close()


def do_set(args):
    filepath = args.file
    if not Path(filepath).exists():
        # Create a new TOML document
        keytree = args.key.split(".")
        doc = tomlkit.document()
        table = doc
        while True:
            k = keytree.pop(0)
            if len(keytree) > 0:
                table[k] = tomlkit.table()
                table = table[k]
            else:
                table[k] = args.value
                break
    else:
        if filepath == "-":
            args.file = sys.stdin
        else:
            args.file = open(filepath, "rb")
        doc = tomlkit.load(args.file)
        keytree = args.key.split(".")
        keytree_traversed = keytree[:-1]
        table = doc
        try:
            while True:
                try:
                    k = keytree_traversed.pop(0)
                except IndexError:
                    break
                try:
                    if (match_index := rx_index.search(k)) and (
                        (index := match_index.group("index")) is not None
                    ):
                        table = table[match_index.group("key")][int(index)]
                    else:
                        table = table[k]
                except NonExistentKey:
                    table[k] = tomlkit.table()
                    table = table[k]
            last_key = keytree[-1]
            if not isinstance(table, AbstractTable):
                print(
                    f"We can only set values in a table. {args.key!r} is not a table key.",
                    file=sys.stderr,
                )
                sys.exit(1)
            table[last_key] = args.value
        finally:
            if isinstance(args.file, io.BufferedIOBase):
                args.file.close()
    if args.file is sys.stdin:
        print(tomlkit.dumps(doc), end="")
    else:
        with open(filepath, "w") as fp:
            tomlkit.dump(doc, fp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", default="-")
    subparsers = parser.add_subparsers()

    parser_set = subparsers.add_parser("set", help="set a toml key")
    parser_set.add_argument("key")
    parser_set.add_argument("value")
    parser_set.set_defaults(func=do_set)

    parser_get = subparsers.add_parser("get", help="get a toml key")
    parser_get.add_argument("key")
    parser_get.set_defaults(func=do_get)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
