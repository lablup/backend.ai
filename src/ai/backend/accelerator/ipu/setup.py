import sys
from pathlib import Path

from Cython.Build import cythonize
from setuptools import setup
from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
from setuptools.extension import Extension
from wheel.wheelfile import WheelFile

exclude_source_files = False

pure_python_mods = (
    "__init__.py",
    "types.py",
)


def _filtered_writestr(self, zinfo_or_arcname, bytes, compress_type=None):
    global exclude_source_files
    if exclude_source_files:
        if isinstance(zinfo_or_arcname, str):
            fn = zinfo_or_arcname
        else:
            fn = zinfo_or_arcname.filename
        if fn.startswith("ai/backend/accelerator/ipu/"):
            if (fn.endswith(".py") and Path(fn).name not in pure_python_mods) or fn.endswith(".c"):  # noqa: W503
                return
    self._orig_writestr(zinfo_or_arcname, bytes, compress_type)


WheelFile._orig_writestr = WheelFile.writestr
WheelFile.writestr = _filtered_writestr


class bdist_wheel(_bdist_wheel):
    _bdist_wheel.user_options.append(
        ("exclude-source-files", None, "remove all .py files from the generated wheel"),
    )

    def initialize_options(self):
        super().initialize_options()
        self.python_tag = None
        self.exclude_source_files = False

    def finalize_options(self):
        global exclude_source_files
        if self.python_tag is None:
            if self.exclude_source_files:
                self.python_tag = f"py{sys.version_info[0]}{sys.version_info[1]}"
            else:
                self.python_tag = f"py{sys.version_info[0]}"
        super().finalize_options()
        exclude_source_files = self.exclude_source_files


setup(
    ext_modules=cythonize(
        [
            Extension(
                f"ai.backend.accelerator.ipu.{path.stem}",
                [f"src/ai/backend/accelerator/ipu/{path.stem}.py"],
            )
            for path in Path("src/ai/backend/accelerator/ipu").glob("*.py")
            if path.name not in pure_python_mods
        ],
        language_level=3,
    ),
    cmdclass={
        "bdist_wheel": bdist_wheel,
    },
)
