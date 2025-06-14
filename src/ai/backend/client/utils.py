import base64
import io
import os
import textwrap
import uuid

from ai.backend.client.output.types import FieldSet, FieldSpec


def dedent(text: str) -> str:
    return textwrap.dedent(text).strip()


def create_connection_field(field_name: str, node_fields: FieldSet) -> FieldSpec:
    """
    Creates a GraphQL connection field specification with standard 'edges' and 'node' structure.
    Useful for building paginated queries where each edge contains a node with specified fields.
    """
    if isinstance(node_fields, (tuple, list)):
        node_fields = FieldSet(node_fields)

    return FieldSpec(
        field_name,
        subfields=FieldSet([
            FieldSpec("edges", subfields=FieldSet([FieldSpec("node", subfields=node_fields)]))
        ]),
    )


def flatten_connection(connection_data: dict) -> list[dict]:
    """
    Flattens a GraphQL Connection structure into a list of node dictionaries.
    Args:
        connection_data (dict): The GraphQL Connection data containing 'edges'.
    Returns:
        list[dict]: A list of node dictionaries extracted from the connection.
    """
    if connection_data is None or "edges" not in connection_data:
        return []
    return [edge["node"] for edge in connection_data["edges"]]


def flatten_connections_in_data(data: dict) -> dict:
    """
    Flattens all connection fields in a nested dictionary.
    If a value is a dictionary containing an 'edges' key, it is flattened using flatten_connection().
    Returns a new dictionary with all connections flattened.
    """
    result = {}

    if data is None:
        return result

    for key, value in data.items():
        if key.endswith("_nodes") and isinstance(value, dict) and "edges" in value:
            result[key] = flatten_connection(value)
            continue
        result[key] = value

    return result


class ProgressReportingReader(io.BufferedReader):
    def __init__(self, file_path, *, tqdm_instance=None):
        super().__init__(open(file_path, "rb"))
        self._filename = os.path.basename(file_path)
        if tqdm_instance is None:
            from tqdm import tqdm

            self._owns_tqdm = True
            self.tqdm = tqdm(
                unit="bytes",
                unit_scale=True,
                total=os.path.getsize(file_path),
            )
        else:
            self._owns_tqdm = False
            self.tqdm = tqdm_instance

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self._owns_tqdm:
            self.tqdm.close()
        self.close()

    def read(self, *args, **kwargs):
        chunk = super().read(*args, **kwargs)
        self.tqdm.set_postfix(file=self._filename, refresh=False)
        self.tqdm.update(len(chunk))
        return chunk

    def read1(self, *args, **kwargs):
        chunk = super().read1(*args, **kwargs)
        self.tqdm.set_postfix(file=self._filename, refresh=False)
        self.tqdm.update(len(chunk))
        return chunk

    def readinto(self, *args, **kwargs):
        count = super().readinto(*args, **kwargs)
        self.tqdm.set_postfix(file=self._filename, refresh=False)
        self.tqdm.update(count)

    def readinto1(self, *args, **kwargs):
        count = super().readinto1(*args, **kwargs)
        self.tqdm.set_postfix(file=self._filename, refresh=False)
        self.tqdm.update(count)


def to_global_id(node_name: str, id: uuid.UUID) -> str:
    """
    Used to generate a global ID for a node in the GraphQL Relay specification.
    Encode the node name and id into a global ID using Base64 encoding.
    """
    return base64.b64encode(f"{node_name}:{str(id)}".encode("utf-8")).decode("ascii")
