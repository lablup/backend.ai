import io
import re
import sys
from pathlib import Path
from typing import Any

import tomlkit
from tomlkit.exceptions import NonExistentKey
from tomlkit.items import AbstractTable

rx_index = re.compile(r"^(?P<key>\w+)(\[(?P<index>\d+)\])?$")


def toml_get(filepath: str, key: str) -> str:
    if filepath == "-":
        file = sys.stdin
    else:
        file = Path(filepath).open()
    doc = tomlkit.load(file)
    keytree = key.split(".")
    keytree_traversed = keytree[:]
    table = doc
    k: str = ""
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
    current_table: Any
    if not Path(filepath).exists():
        # Create a new TOML document
        keytree = key.split(".")
        doc = tomlkit.document()
        current_table = doc
        while True:
            k = keytree.pop(0)
            if len(keytree) > 0:
                current_table[k] = tomlkit.table()
                current_table = current_table[k]
            else:
                current_table[k] = value
                break
    else:
        if filepath == "-":
            file = sys.stdin
        else:
            file = Path(filepath).open()
        doc = tomlkit.load(file)
        keytree = key.split(".")
        keytree_traversed = keytree[:-1]
        current_table = doc
        k = ""
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
                        current_table = current_table[match_index.group("key")][int(index)]
                    else:
                        current_table = current_table[k]
                except NonExistentKey:
                    current_table[k] = tomlkit.table()
                    current_table = current_table[k]
            last_key = keytree[-1]
            if not isinstance(current_table, AbstractTable):
                raise ValueError(
                    f"We can only set values in a table. {key!r} is not a table key.",
                )
            current_table[last_key] = value
        finally:
            if isinstance(file, io.BufferedIOBase):
                file.close()
    with Path(filepath).open("w") as fp:
        tomlkit.dump(doc, fp)
