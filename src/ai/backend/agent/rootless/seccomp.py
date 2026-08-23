"""Compile Backend.AI's seccomp profile to classic BPF, for runtimes that have no runc.

Every other backend gets seccomp for free: it hands the OCI spec's ``linux.seccomp`` to runc (or
to dockerd), which compiles it with libseccomp and installs it at container start. enroot has
neither — upstream states plainly that it *"removes much of the isolation [containers] inherently
provide"* and its only mention of seccomp anywhere is a check that the kernel supports it. So the
agent compiles the profile itself and the container installs it before the user's command runs.

Doing it here rather than leaning on BAI's `jail` matters for one concrete reason beyond strength:
jail ships as an **x86_64-only** binary, while enroot ships aarch64 for every flavor and GH200-class
nodes are a mainstream enroot target. A BPF filter is architecture-independent, so this is the only
route to any syscall filtering there at all.

The output is a packed ``struct sock_filter[]``, ready for ``prctl(PR_SET_SECCOMP,
SECCOMP_MODE_FILTER, &sock_fprog)``. See ``seccomp_installer.py`` for the in-container side.
"""

from __future__ import annotations

import struct
from collections.abc import Mapping, Sequence
from typing import Any, Final

from ai.backend.agent.rootless.syscall_tables import SYSCALL_TABLES

# --- classic BPF, as seccomp uses it (linux/bpf_common.h) ---------------------------------------
_LD: Final = 0x00
_ALU: Final = 0x04
_JMP: Final = 0x05
_RET: Final = 0x06
_W: Final = 0x00
_ABS: Final = 0x20
_K: Final = 0x00
_JEQ: Final = 0x10
_JGT: Final = 0x20
_JGE: Final = 0x30
_JSET: Final = 0x40
_AND: Final = 0x50

# --- seccomp (linux/seccomp.h) ------------------------------------------------------------------
SECCOMP_RET_KILL_PROCESS: Final = 0x80000000
SECCOMP_RET_TRAP: Final = 0x00030000
SECCOMP_RET_ERRNO: Final = 0x00050000
SECCOMP_RET_LOG: Final = 0x7FFC0000
SECCOMP_RET_ALLOW: Final = 0x7FFF0000

# struct seccomp_data { int nr; __u32 arch; __u64 ip; __u64 args[6]; }
_OFF_NR: Final = 0
_OFF_ARCH: Final = 4
_OFF_ARGS: Final = 16

# AUDIT_ARCH_* (linux/audit.h). The filter pins the architecture: on x86_64 a process can issue
# i386 or x32 syscalls, where the SAME number means a DIFFERENT call — an allowlist checked without
# this is trivially bypassed by switching ABI.
_AUDIT_ARCH: Final[dict[str, int]] = {
    "x86_64": 0xC000003E,
    "aarch64": 0xC00000B7,
}

_ACTIONS: Final[dict[str, int]] = {
    "SCMP_ACT_KILL": SECCOMP_RET_KILL_PROCESS,
    "SCMP_ACT_KILL_PROCESS": SECCOMP_RET_KILL_PROCESS,
    "SCMP_ACT_TRAP": SECCOMP_RET_TRAP,
    "SCMP_ACT_ERRNO": SECCOMP_RET_ERRNO,
    "SCMP_ACT_LOG": SECCOMP_RET_LOG,
    "SCMP_ACT_ALLOW": SECCOMP_RET_ALLOW,
}
_DEFAULT_ERRNO: Final = 1  # EPERM, matching the profile's own defaultErrnoRet
_MAX_JUMP: Final = 0xFF  # classic BPF jt/jf are 8-bit
_U32: Final = 0xFFFFFFFF


class SeccompCompileError(Exception):
    """The profile cannot be turned into a filter. Never silently degrade: a filter that quietly
    dropped a rule would look installed and enforce less than it claims."""


class _Program:
    """A label-addressed BPF program.

    Jump targets are resolved in a fixup pass rather than computed by hand: seccomp's jt/jf are
    *relative* 8-bit offsets, and an off-by-one there does not fail loudly — it silently sends a
    syscall to the wrong verdict.
    """

    def __init__(self) -> None:
        self._insns: list[tuple[int, Any, Any, int]] = []
        self._labels: dict[str, int] = {}

    def label(self, name: str) -> None:
        if name in self._labels:
            raise SeccompCompileError(f"duplicate label {name}")
        self._labels[name] = len(self._insns)

    def emit(self, code: int, jt: Any = 0, jf: Any = 0, k: int = 0) -> None:
        self._insns.append((code, jt, jf, k))

    def load_u32(self, offset: int) -> None:
        self.emit(_LD | _W | _ABS, k=offset)

    def ret(self, value: int) -> None:
        self.emit(_RET | _K, k=value)

    def assemble(self) -> bytes:
        out = bytearray()
        for index, (code, jt, jf, k) in enumerate(self._insns):
            out += struct.pack("<HBBI", code, self._offset(jt, index), self._offset(jf, index), k)
        return bytes(out)

    def _offset(self, target: Any, index: int) -> int:
        if isinstance(target, int):
            return target
        if target not in self._labels:
            raise SeccompCompileError(f"unresolved label {target}")
        distance = self._labels[target] - (index + 1)
        if not 0 <= distance <= _MAX_JUMP:
            # Reachable only if the profile grows far beyond Docker's; splitting into a jump table
            # would be the fix. Refuse rather than emit a filter that jumps somewhere else.
            raise SeccompCompileError(f"jump to {target} is {distance} instructions, out of range")
        return distance

    def __len__(self) -> int:
        return len(self._insns)


def _action_value(action: str, errno_ret: int | None) -> int:
    try:
        value = _ACTIONS[action]
    except KeyError:
        raise SeccompCompileError(f"unsupported seccomp action {action}") from None
    if value == SECCOMP_RET_ERRNO:
        value |= (errno_ret if errno_ret is not None else _DEFAULT_ERRNO) & 0xFFFF
    return value


def _emit_arg_check(prog: _Program, arg: Mapping[str, Any], mismatch: str, tag: str) -> None:
    """Jump to ``mismatch`` unless the syscall argument satisfies ``arg``; fall through if it does.

    A seccomp argument is 64-bit but classic BPF registers are 32-bit, so every comparison is done
    as a high-word/low-word pair. Getting that wrong is the classic way to write a filter that
    passes a crafted 64-bit value.
    """
    index = int(arg["index"])
    if not 0 <= index <= 5:
        raise SeccompCompileError(f"argument index {index} out of range")
    low_off = _OFF_ARGS + 8 * index
    high_off = low_off + 4
    op = str(arg["op"])
    value = int(arg["value"]) & 0xFFFFFFFFFFFFFFFF
    v_low, v_high = value & _U32, (value >> 32) & _U32

    if op == "SCMP_CMP_MASKED_EQ":
        # (arg & mask) == valueTwo. `value` is the mask; OCI calls the expected result valueTwo.
        expected = int(arg.get("valueTwo") or 0) & 0xFFFFFFFFFFFFFFFF
        for off, mask_word, want in (
            (high_off, v_high, (expected >> 32) & _U32),
            (low_off, v_low, expected & _U32),
        ):
            prog.load_u32(off)
            prog.emit(_ALU | _AND | _K, k=mask_word)
            prog.emit(_JMP | _JEQ | _K, jt=0, jf=mismatch, k=want)
        return

    if op in ("SCMP_CMP_EQ", "SCMP_CMP_NE"):
        match = f"{tag}.eq"
        prog.load_u32(high_off)
        prog.emit(_JMP | _JEQ | _K, jt=0, jf=(mismatch if op == "SCMP_CMP_EQ" else match), k=v_high)
        prog.load_u32(low_off)
        prog.emit(_JMP | _JEQ | _K, jt=0, jf=(mismatch if op == "SCMP_CMP_EQ" else match), k=v_low)
        if op == "SCMP_CMP_NE":
            # Both words equal => the values ARE equal => NE fails.
            prog.emit(_JMP | _JEQ | _K, jt=mismatch, jf=mismatch, k=0)
            prog.label(match)
        return

    if op in ("SCMP_CMP_LT", "SCMP_CMP_LE", "SCMP_CMP_GT", "SCMP_CMP_GE"):
        ordered = f"{tag}.ok"
        greater = op in ("SCMP_CMP_GT", "SCMP_CMP_GE")
        inclusive = op in ("SCMP_CMP_LE", "SCMP_CMP_GE")
        prog.load_u32(high_off)
        # Decide on the high word first; only a tie falls through to the low word.
        if greater:
            prog.emit(_JMP | _JGT | _K, jt=ordered, jf=0, k=v_high)
        else:
            prog.emit(_JMP | _JGE | _K, jt=mismatch, jf=0, k=v_high + 1)
        prog.emit(_JMP | _JEQ | _K, jt=0, jf=(mismatch if greater else ordered), k=v_high)
        prog.load_u32(low_off)
        # BPF only has JGT/JGE, so the strict/inclusive distinction is carried by the opcode and
        # the branch sense, never by the constant.
        low_op = _JGE if (greater and inclusive) or (not greater and not inclusive) else _JGT
        if greater:
            prog.emit(_JMP | low_op | _K, jt=ordered, jf=mismatch, k=v_low)
        else:
            prog.emit(_JMP | low_op | _K, jt=mismatch, jf=ordered, k=v_low)
        prog.label(ordered)
        return

    raise SeccompCompileError(f"unsupported comparison {op}")


def compile_profile(oci: Mapping[str, Any], *, arch: str) -> bytes:
    """Compile an OCI ``linux.seccomp`` object into a packed BPF program for ``arch``.

    Rules are emitted deny-before-allow. The profile is an allowlist with a handful of explicit
    denials (``clone3`` for a container without CAP_SYS_ADMIN), and an explicit denial must not be
    reachable-around by a broader allow rule listed earlier.

    Syscall names the architecture does not have are skipped, not an error: the profile is written
    for every architecture at once, so it names `access`/`chmod`/`dup2` (absent on aarch64) and
    `arm_sync_file_range` (absent on x86_64) side by side. runc/libseccomp skip unresolvable names
    the same way.
    """
    audit_arch = _AUDIT_ARCH.get(arch)
    table = SYSCALL_TABLES.get(arch)
    if audit_arch is None or table is None:
        raise SeccompCompileError(f"no seccomp syscall table for {arch}")

    default = _action_value(
        str(oci.get("defaultAction", "SCMP_ACT_ERRNO")), oci.get("defaultErrnoRet")
    )
    rules: Sequence[Mapping[str, Any]] = list(oci.get("syscalls") or [])
    denies = [r for r in rules if r.get("action") != "SCMP_ACT_ALLOW"]
    allows = [r for r in rules if r.get("action") == "SCMP_ACT_ALLOW"]

    prog = _Program()
    # Pin the ABI before anything else (see _AUDIT_ARCH). The kill sits inline right after the
    # check rather than at the end of the program: jt/jf are 8-bit, and the real profile is ~670
    # instructions long, so a jump to a trailer would be out of range.
    prog.load_u32(_OFF_ARCH)
    prog.emit(_JMP | _JEQ | _K, jt=1, jf=0, k=audit_arch)
    # An unexpected ABI is not a policy question — nothing legitimate reaches here.
    prog.ret(SECCOMP_RET_KILL_PROCESS)
    prog.load_u32(_OFF_NR)
    for rule_index, rule in enumerate([*denies, *allows]):
        action = _action_value(str(rule["action"]), rule.get("errnoRet"))
        args = rule.get("args") or []
        for name in rule.get("names") or []:
            number = table.get(name)
            if number is None:
                continue
            tag = f"r{rule_index}_{name}"
            nomatch = f"{tag}.next"
            prog.emit(_JMP | _JEQ | _K, jt=0, jf=nomatch, k=number)
            for arg_index, arg in enumerate(args):
                _emit_arg_check(prog, arg, nomatch, f"{tag}.a{arg_index}")
            prog.ret(action)
            prog.label(nomatch)
            if args:
                # The arg checks clobbered the accumulator; the next rule compares the syscall
                # number again, so put it back.
                prog.load_u32(_OFF_NR)
    prog.ret(default)
    return prog.assemble()
