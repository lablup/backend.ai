import io
import os

import click
from tqdm import tqdm


def validate_key_value(ctx, param, value):
    key_value_pairs = value.split(",")
    for pair in key_value_pairs:
        if "=" not in pair:
            raise click.BadParameter(
                'Invalid format. Each key-value pair should be in the format "key=value".'
            )
    return value


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
