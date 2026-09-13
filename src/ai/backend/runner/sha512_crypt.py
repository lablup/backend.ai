"""
Generate a SHA-512 crypt(3) hash ($6$) for /etc/shadow without relying on the container image.

entrypoint.sh uses this when the image has no ``chpasswd``. The password is read from stdin so that
it never appears in the process arguments. The implementation follows the "Unix crypt using SHA-256
and SHA-512" specification by Ulrich Drepper and produces output identical to glibc's crypt(3).

This module runs under the kernel runner's bundled Python (not the image's), so it depends on
the standard library only.
"""

import argparse
import hashlib
import secrets
import sys

ITOA64 = b"./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
DEFAULT_ROUNDS = 5000
MIN_ROUNDS = 1000
MAX_ROUNDS = 999999999
SALT_LEN = 16

# (byte index triplets, number of output characters) in the order mandated by the specification.
ENCODE_ORDER: tuple[tuple[int | None, int | None, int, int], ...] = (
    (0, 21, 42, 4),
    (22, 43, 1, 4),
    (44, 2, 23, 4),
    (3, 24, 45, 4),
    (25, 46, 4, 4),
    (47, 5, 26, 4),
    (6, 27, 48, 4),
    (28, 49, 7, 4),
    (50, 8, 29, 4),
    (9, 30, 51, 4),
    (31, 52, 10, 4),
    (53, 11, 32, 4),
    (12, 33, 54, 4),
    (34, 55, 13, 4),
    (56, 14, 35, 4),
    (15, 36, 57, 4),
    (37, 58, 16, 4),
    (59, 17, 38, 4),
    (18, 39, 60, 4),
    (40, 61, 19, 4),
    (62, 20, 41, 4),
    (None, None, 63, 2),
)


def _b64_from_24bit(b2: int, b1: int, b0: int, n: int) -> bytes:
    value = (b2 << 16) | (b1 << 8) | b0
    out = bytearray()
    for _ in range(n):
        out.append(ITOA64[value & 0x3F])
        value >>= 6
    return bytes(out)


def _repeat_to_length(block: bytes, length: int) -> bytes:
    if length == 0:
        return b""
    return (block * (length // len(block) + 1))[:length]


def generate_salt(length: int = SALT_LEN) -> str:
    return "".join(chr(ITOA64[secrets.randbelow(len(ITOA64))]) for _ in range(length))


def sha512_crypt(password: str | bytes, salt: str | bytes, rounds: int = DEFAULT_ROUNDS) -> str:
    """
    Return the crypt(3) string for *password* using SHA-512 with the given *salt*.

    The salt is truncated to 16 characters as glibc does. When *rounds* differs from the
    default, a ``rounds=N$`` marker is emitted as required by the specification.
    """
    if isinstance(password, str):
        password = password.encode("utf-8")
    if isinstance(salt, str):
        salt = salt.encode("utf-8")
    salt = salt[:SALT_LEN]
    rounds = max(MIN_ROUNDS, min(MAX_ROUNDS, int(rounds)))
    pw_len = len(password)

    digest_b = hashlib.sha512(password + salt + password).digest()

    ctx_a = hashlib.sha512()
    ctx_a.update(password)
    ctx_a.update(salt)
    ctx_a.update(_repeat_to_length(digest_b, pw_len))
    bits = pw_len
    while bits > 0:
        ctx_a.update(digest_b if bits & 1 else password)
        bits >>= 1
    digest_a = ctx_a.digest()

    digest_dp = hashlib.sha512(password * pw_len).digest()
    seq_p = _repeat_to_length(digest_dp, pw_len)

    digest_ds = hashlib.sha512(salt * (16 + digest_a[0])).digest()
    seq_s = _repeat_to_length(digest_ds, len(salt))

    digest_c = digest_a
    for i in range(rounds):
        ctx_c = hashlib.sha512()
        ctx_c.update(seq_p if i & 1 else digest_c)
        if i % 3:
            ctx_c.update(seq_s)
        if i % 7:
            ctx_c.update(seq_p)
        ctx_c.update(digest_c if i & 1 else seq_p)
        digest_c = ctx_c.digest()

    encoded = bytearray()
    for i2, i1, i0, n in ENCODE_ORDER:
        b2 = digest_c[i2] if i2 is not None else 0
        b1 = digest_c[i1] if i1 is not None else 0
        encoded.extend(_b64_from_24bit(b2, b1, digest_c[i0], n))

    prefix = b"$6$"
    if rounds != DEFAULT_ROUNDS:
        prefix += f"rounds={rounds}$".encode("ascii")
    return (prefix + salt + b"$" + bytes(encoded)).decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print the SHA-512 crypt hash of the password read from stdin.",
    )
    parser.add_argument(
        "--salt",
        default=None,
        help="salt to use (default: random 16 characters)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=DEFAULT_ROUNDS,
        help="number of hashing rounds (default: %(default)s)",
    )
    args = parser.parse_args()

    password = sys.stdin.readline()
    password = password.removesuffix("\n")
    if not password:
        print("sha512_crypt: empty password on stdin", file=sys.stderr)
        return 1
    salt = args.salt if args.salt is not None else generate_salt()
    print(sha512_crypt(password, salt, args.rounds))
    return 0


if __name__ == "__main__":
    sys.exit(main())
