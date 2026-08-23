"""Semantics of the rootless backends' seccomp compiler.

The compiler emits a BPF program nobody can eyeball, and a mistake in it does not fail loudly — a
mis-resolved jump or a half-checked 64-bit argument produces a filter that installs cleanly and
enforces something other than the profile. So these tests *run* the compiled program against
synthetic ``seccomp_data`` with a small interpreter, and assert the verdict rather than the
encoding.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.containerd.agent import _docker_seccomp_to_oci
from ai.backend.agent.rootless.seccomp import (
    SECCOMP_RET_ALLOW,
    SECCOMP_RET_ERRNO,
    SECCOMP_RET_KILL_PROCESS,
    SeccompCompileError,
    compile_profile,
)
from ai.backend.agent.rootless.syscall_tables import SYSCALL_TABLES

_AUDIT_X86_64 = 0xC000003E
_U32 = 0xFFFFFFFF


def _seccomp_data(nr: int, arch: int = _AUDIT_X86_64, args: list[int] | None = None) -> bytes:
    """struct seccomp_data { int nr; __u32 arch; __u64 ip; __u64 args[6]; }"""
    filled = list(args or [])[:6] + [0] * (6 - len(args or []))
    return struct.pack("<IIQ6Q", nr & _U32, arch, 0, *filled)


def _run(program: bytes, data: bytes) -> int:
    """Interpret the classic-BPF subset the compiler emits, and return the seccomp verdict."""
    insns = [struct.unpack_from("<HBBI", program, i) for i in range(0, len(program), 8)]
    acc, pc = 0, 0
    for _ in range(10000):  # a filter must terminate; this only catches a compiler bug
        code, jt, jf, k = insns[pc]
        pc += 1
        if code == 0x20:  # BPF_LD | BPF_W | BPF_ABS
            acc = struct.unpack_from("<I", data, k)[0]
        elif code == 0x54:  # BPF_ALU | BPF_AND | BPF_K
            acc &= k
        elif code == 0x06:  # BPF_RET | BPF_K
            return int(k)
        elif code in (0x15, 0x25, 0x35):  # JMP JEQ / JGT / JGE with K
            taken = {0x15: acc == k, 0x25: acc > k, 0x35: acc >= k}[code]
            pc += jt if taken else jf
        else:
            raise AssertionError(f"interpreter does not know opcode {code:#x}")
    raise AssertionError("filter did not terminate")


def _verdict(
    program: bytes,
    name: str,
    *,
    arch: str = "x86_64",
    args: list[int] | None = None,
    audit_arch: int = _AUDIT_X86_64,
) -> int:
    return _run(program, _seccomp_data(SYSCALL_TABLES[arch][name], audit_arch, args))


def _profile(syscalls: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
    return {"defaultAction": "SCMP_ACT_ERRNO", "defaultErrnoRet": 1, "syscalls": syscalls, **extra}


class TestBasicVerdicts:
    def test_listed_syscall_is_allowed(self) -> None:
        prog = compile_profile(
            _profile([{"names": ["read", "write"], "action": "SCMP_ACT_ALLOW"}]), arch="x86_64"
        )
        assert _verdict(prog, "read") == SECCOMP_RET_ALLOW
        assert _verdict(prog, "write") == SECCOMP_RET_ALLOW

    def test_unlisted_syscall_gets_the_default(self) -> None:
        prog = compile_profile(
            _profile([{"names": ["read"], "action": "SCMP_ACT_ALLOW"}]), arch="x86_64"
        )
        assert _verdict(prog, "keyctl") == SECCOMP_RET_ERRNO | 1

    def test_a_foreign_abi_is_killed(self) -> None:
        """On x86_64 the same number means a different call under i386/x32; an allowlist that does
        not pin the ABI is bypassed by switching it."""
        prog = compile_profile(
            _profile([{"names": ["read"], "action": "SCMP_ACT_ALLOW"}]), arch="x86_64"
        )
        assert _verdict(prog, "read", audit_arch=0x40000003) == SECCOMP_RET_KILL_PROCESS

    def test_explicit_denial_beats_a_broader_allow(self) -> None:
        prog = compile_profile(
            _profile([
                {"names": ["clone3"], "action": "SCMP_ACT_ALLOW"},
                {"names": ["clone3"], "action": "SCMP_ACT_ERRNO", "errnoRet": 38},
            ]),
            arch="x86_64",
        )
        assert _verdict(prog, "clone3") == SECCOMP_RET_ERRNO | 38

    def test_names_absent_on_the_architecture_are_skipped(self) -> None:
        """The profile names every architecture's syscalls at once; `access` does not exist on
        aarch64 and must not abort the compile."""
        assert "access" not in SYSCALL_TABLES["aarch64"]
        prog = compile_profile(
            _profile([{"names": ["access", "read"], "action": "SCMP_ACT_ALLOW"}]), arch="aarch64"
        )
        assert _run(prog, _seccomp_data(SYSCALL_TABLES["aarch64"]["read"], 0xC00000B7))


class TestArgumentMatching:
    def _sock(self, ops: list[dict[str, Any]]) -> bytes:
        return compile_profile(
            _profile([{"names": ["socket"], "action": "SCMP_ACT_ALLOW", "args": ops}]),
            arch="x86_64",
        )

    def test_eq(self) -> None:
        prog = self._sock([{"index": 0, "value": 8, "op": "SCMP_CMP_EQ"}])
        assert _verdict(prog, "socket", args=[8]) == SECCOMP_RET_ALLOW
        assert _verdict(prog, "socket", args=[9]) == SECCOMP_RET_ERRNO | 1

    def test_lt(self) -> None:
        prog = self._sock([{"index": 0, "value": 38, "op": "SCMP_CMP_LT"}])
        assert _verdict(prog, "socket", args=[37]) == SECCOMP_RET_ALLOW
        assert _verdict(prog, "socket", args=[38]) == SECCOMP_RET_ERRNO | 1
        assert _verdict(prog, "socket", args=[39]) == SECCOMP_RET_ERRNO | 1

    def test_gt(self) -> None:
        prog = self._sock([{"index": 0, "value": 40, "op": "SCMP_CMP_GT"}])
        assert _verdict(prog, "socket", args=[41]) == SECCOMP_RET_ALLOW
        assert _verdict(prog, "socket", args=[40]) == SECCOMP_RET_ERRNO | 1
        assert _verdict(prog, "socket", args=[39]) == SECCOMP_RET_ERRNO | 1

    def test_masked_eq(self) -> None:
        """Docker's clone rule: none of the namespace flags may be set."""
        prog = compile_profile(
            _profile([
                {
                    "names": ["clone"],
                    "action": "SCMP_ACT_ALLOW",
                    "args": [{"index": 0, "value": 0x7E020000, "op": "SCMP_CMP_MASKED_EQ"}],
                }
            ]),
            arch="x86_64",
        )
        assert _verdict(prog, "clone", args=[0x00000F00]) == SECCOMP_RET_ALLOW
        assert _verdict(prog, "clone", args=[0x10000000]) == SECCOMP_RET_ERRNO | 1  # CLONE_NEWUSER

    def test_a_high_word_cannot_sneak_past_a_32_bit_comparison(self) -> None:
        """Arguments are 64-bit and BPF registers are 32-bit. Comparing only the low word lets
        0x1_0000_0008 pass an `== 8` check."""
        prog = self._sock([{"index": 0, "value": 8, "op": "SCMP_CMP_EQ"}])
        assert _verdict(prog, "socket", args=[0x100000008]) == SECCOMP_RET_ERRNO | 1
        lt = self._sock([{"index": 0, "value": 38, "op": "SCMP_CMP_LT"}])
        assert _verdict(lt, "socket", args=[0x100000001]) == SECCOMP_RET_ERRNO | 1

    def test_a_rule_that_does_not_match_falls_through_to_later_rules(self) -> None:
        """After an argument check the accumulator holds an argument, not the syscall number; a
        later rule that compared it as-is would match the wrong call."""
        prog = compile_profile(
            _profile([
                {
                    "names": ["socket"],
                    "action": "SCMP_ACT_ALLOW",
                    "args": [{"index": 0, "value": 2, "op": "SCMP_CMP_EQ"}],
                },
                {"names": ["read"], "action": "SCMP_ACT_ALLOW"},
            ]),
            arch="x86_64",
        )
        assert _verdict(prog, "socket", args=[2]) == SECCOMP_RET_ALLOW
        assert _verdict(prog, "socket", args=[3]) == SECCOMP_RET_ERRNO | 1
        assert _verdict(prog, "read") == SECCOMP_RET_ALLOW


class TestTheRealProfile:
    """The shipped profile, resolved and compiled for every architecture the backend claims.

    This is what caught the first cut: jt/jf are 8-bit, and with ~670 instructions a jump to a
    trailer at the end of the program is out of range. A toy profile never reaches that size.
    """

    @pytest.mark.parametrize("arch", ["x86_64", "aarch64"])
    def test_it_compiles_and_behaves(self, arch: str) -> None:
        raw = json.loads(Path("src/ai/backend/runner/default-seccomp.json").read_text())
        caps = frozenset({"CAP_CHOWN", "CAP_SETUID", "CAP_SETGID"})
        oci = _docker_seccomp_to_oci(raw, caps=caps, arch=arch)
        prog = compile_profile(oci, arch=arch)
        assert len(prog) // 8 < 4096, "BPF programs are capped at 4096 instructions"

        audit = {"x86_64": 0xC000003E, "aarch64": 0xC00000B7}[arch]
        table = SYSCALL_TABLES[arch]
        # Ordinary calls the runner makes constantly must survive.
        for name in ("read", "write", "execve", "openat", "mmap"):
            assert _run(prog, _seccomp_data(table[name], audit)) == SECCOMP_RET_ALLOW, name
        # ...and the ones the profile exists to deny must not.
        for name in ("keyctl", "add_key", "request_key"):
            assert _run(prog, _seccomp_data(table[name], audit)) != SECCOMP_RET_ALLOW, name

    def test_a_container_without_cap_sys_admin_cannot_clone3(self) -> None:
        """The profile's one explicit denial; `excludes.caps` must actually resolve."""
        raw = json.loads(Path("src/ai/backend/runner/default-seccomp.json").read_text())
        oci = _docker_seccomp_to_oci(raw, caps=frozenset({"CAP_CHOWN"}), arch="x86_64")
        prog = compile_profile(oci, arch="x86_64")
        assert _verdict(prog, "clone3") == SECCOMP_RET_ERRNO | 38  # ENOSYS


class TestRefusals:
    def test_unknown_architecture(self) -> None:
        with pytest.raises(SeccompCompileError):
            compile_profile(_profile([]), arch="riscv64")

    def test_unknown_action(self) -> None:
        with pytest.raises(SeccompCompileError):
            compile_profile(
                _profile([{"names": ["read"], "action": "SCMP_ACT_NOTIFY"}]), arch="x86_64"
            )

    def test_unknown_comparison(self) -> None:
        with pytest.raises(SeccompCompileError):
            compile_profile(
                _profile([
                    {
                        "names": ["read"],
                        "action": "SCMP_ACT_ALLOW",
                        "args": [{"index": 0, "value": 1, "op": "SCMP_CMP_WHATEVER"}],
                    }
                ]),
                arch="x86_64",
            )
