import io
import os

import click
from tqdm import tqdm


def validate_key_value(ctx, param, option_value):
    key_value_pairs = option_value.split(",")
    if len(key_value_pairs) > 50:
        raise click.BadParameter("Too many key-value pairs (maximum 50).")
    for pair in key_value_pairs:
        if "=" not in pair:
            raise click.BadParameter(
                'Invalid format. Each key-value pair should be in the format "key=value".'
            )
        key, value = pair.split("=", 1)
        if not key:
            raise click.BadParameter("Empty key is not allowed.")
        if not value:
            raise click.BadParameter("Empty value is not allowed.")
        if len(key) > 128:
            raise click.BadParameter("Key length should be less than 128 characters.")
        if len(value) > 256:
            raise click.BadParameter("Value length should be less than 256 characters.")
    return option_value


class ProgressReportingReader(io.BufferedReader):
    def __init__(self, file_path, *, tqdm_instance=None):
        super().__init__(open(file_path, "rb"))
        self._filename = os.path.basename(file_path)
        if tqdm_instance is None:
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
