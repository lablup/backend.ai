import io
import re
import sys
from pathlib import Path

import tomlkit
from tomlkit.exceptions import NonExistentKey
from tomlkit.items import AbstractTable

rx_index = re.compile(r"^(?P<key>\w+)(\[(?P<index>\d+)\])?$")


def toml_get(filepath: str, key: str) -> str:
    if filepath == "-":
        file = sys.stdin
    else:
        file = open(filepath, "r")
    doc = tomlkit.load(file)
    keytree = key.split(".")
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
                table = table[match_index.group("key")][int(index)]  # type: ignore
            else:
                table = table[k]  # type: ignore
        return table  # type: ignore
    except NonExistentKey:
        raise
    finally:
        if isinstance(file, io.BufferedIOBase):
            file.close()


def toml_set(filepath: str, key: str, value: str) -> None:
    if not Path(filepath).exists():
        # Create a new TOML document
        keytree = key.split(".")
        doc = tomlkit.document()
        table = doc
        while True:
            k = keytree.pop(0)
            if len(keytree) > 0:
                table[k] = tomlkit.table()  # type: ignore
                table = table[k]  # type: ignore
            else:
                table[k] = value  # type: ignore
                break
    else:
        if filepath == "-":
            file = sys.stdin
        else:
            file = open(filepath, "r")
        doc = tomlkit.load(file)
        keytree = key.split(".")
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
                        table = table[match_index.group("key")][int(index)]  # type: ignore
                    else:
                        table = table[k]  # type: ignore
                except NonExistentKey:
                    table[k] = tomlkit.table()  # type: ignore
                    table = table[k]  # type: ignore
            last_key = keytree[-1]
            if not isinstance(table, AbstractTable):
                raise ValueError(
                    f"We can only set values in a table. {key!r} is not a table key.",
                )
            table[last_key] = value
        finally:
            if isinstance(file, io.BufferedIOBase):
                file.close()
    with open(filepath, "w") as fp:
        tomlkit.dump(doc, fp)
