"""Regenerate ``ai.backend.agent.enroot.syscall_tables`` from the kernel's uapi headers.

The enroot backend compiles Backend.AI's seccomp profile to BPF itself (no libseccomp, no runc),
and BPF speaks syscall *numbers*. Nothing in the Python stdlib knows them, so the table is a
checked-in artifact — the same choice libseccomp makes.

Usage (needs linux-libc-dev installed):
    python scripts/codegen/gen_syscall_tables.py > \
        src/ai/backend/agent/enroot/syscall_tables.py

x86_64 has its own table; aarch64 uses the asm-generic one. A name absent from an architecture's
header genuinely does not exist there (aarch64 has no `access`/`chmod`/`dup2`, only the `*at`
forms), so callers must treat a missing name as "no such syscall here" and skip it — which is also
what runc/libseccomp do with an unresolvable name.
"""

import re
import sys
from pathlib import Path

_SOURCES = {
    "x86_64": [
        "/usr/include/x86_64-linux-gnu/asm/unistd_64.h",
        "/usr/include/asm/unistd_64.h",
    ],
    "aarch64": ["/usr/include/asm-generic/unistd.h"],
}
_DEFINE = re.compile(r"#define\s+(__NR3264_\w+|__NR_\w+)\s+(.+?)\s*$")


def parse(paths: list[str]) -> dict[str, int]:
    for path in paths:
        if Path(path).exists():
            break
    else:
        raise SystemExit(f"none of these headers exist: {paths}")
    direct: dict[str, int] = {}
    alias: dict[str, str] = {}
    for line in Path(path).read_text().splitlines():
        m = _DEFINE.match(line.strip())
        if not m:
            continue
        name = m.group(1).replace("__NR3264_", "").replace("__NR_", "")
        value = m.group(2).strip()
        if value.isdigit():
            direct[name] = int(value)
        else:
            alias[name] = value.replace("__NR3264_", "").replace("__NR_", "")
    for name, target in alias.items():
        if target in direct:
            direct.setdefault(name, direct[target])
    return direct


def main() -> None:
    out = [
        '"""Syscall name -> number, per architecture. GENERATED — do not edit.',
        "",
        "Regenerate with ``scripts/codegen/gen_syscall_tables.py``; see that script for why this",
        "is checked in rather than derived at runtime.",
        '"""',
        "",
        "from typing import Final",
        "",
    ]
    for arch, paths in _SOURCES.items():
        table = parse(paths)
        out.append(f"SYSCALLS_{arch.upper()}: Final[dict[str, int]] = {{")
        for name, number in sorted(table.items(), key=lambda kv: kv[1]):
            out.append(f'    "{name}": {number},')
        out.append("}")
        out.append("")
    out += [
        "SYSCALL_TABLES: Final[dict[str, dict[str, int]]] = {",
        '    "x86_64": SYSCALLS_X86_64,',
        '    "aarch64": SYSCALLS_AARCH64,',
        "}",
    ]
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
