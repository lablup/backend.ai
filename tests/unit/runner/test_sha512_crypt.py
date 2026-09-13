import pytest

from ai.backend.runner import sha512_crypt

# Reference vectors from the SHA-crypt specification (Ulrich Drepper), identical to glibc crypt(3).
SPEC_VECTORS = [
    (
        "Hello world!",
        "saltstring",
        5000,
        "$6$saltstring$svn8UoSVapNtMuq1ukKS4tPQd8iKwSMHWjl/O817G3uBnIFNjnQJuesI68u4OTLiBFdcbYEdFCoEOfaS35inz1",
    ),
    (
        "Hello world!",
        "saltstringsaltstring",
        10000,
        "$6$rounds=10000$saltstringsaltst$OW1/O6BYHV6BcXZu8QVeXbDWra3Oeqh0sbHbbMCVNSnCM/UrjmM0Dp8vOuZeHBy/YTBmSK6H9qs/y3RnOaw5v.",
    ),
    (
        "This is just a test",
        "toolongsaltstring",
        5000,
        "$6$toolongsaltstrin$lQ8jolhgVRVhY4b5pZKaysCLi0QBxGoNeKQzQ3glMhwllF7oGDZxUhx1yxdYcz/e1JSbq3y6JMxxl8audkUEm0",
    ),
    (
        "a very much longer text to encrypt.  This one even stretches over morethan one line.",
        "anotherlongsaltstring",
        1400,
        "$6$rounds=1400$anotherlongsalts$POfYwTEok97VWcjxIiSOjiykti.o/pQs.wPvMxQ6Fm7I6IoYN3CmLs66x9t0oSwbtEW7o7UmJEiDwGqd8p4ur1",
    ),
    (
        "we have a short salt string but not a short password",
        "short",
        77777,
        "$6$rounds=77777$short$WuQyW2YR.hBNpjjRhpYD/ifIw05xdfeEyQoMxIXbkvr0gge1a1x3yRULJ5CCaUeOxFmtlcGZelFl5CxtgfiAc0",
    ),
    (
        "a short string",
        "asaltof16chars..",
        123456,
        "$6$rounds=123456$asaltof16chars..$BtCwjqMJGx5hrJhZywWvt0RLE8uZ4oPwcelCjmw2kSYu.Ec6ycULevoBK25fs2xXgMNrCzIMVcgEJAstJeonj1",
    ),
]


@pytest.mark.parametrize("password,salt,rounds,expected", SPEC_VECTORS)
def test_matches_specification_vectors(
    password: str, salt: str, rounds: int, expected: str
) -> None:
    assert sha512_crypt.sha512_crypt(password, salt, rounds) == expected


def test_salt_is_truncated_to_16_characters() -> None:
    result = sha512_crypt.sha512_crypt("pw", "0123456789abcdefXYZ")
    assert result.startswith("$6$0123456789abcdef$")


def test_default_rounds_omit_rounds_marker() -> None:
    assert sha512_crypt.sha512_crypt("pw", "salt").startswith("$6$salt$")


def test_rounds_are_clamped_to_minimum() -> None:
    assert sha512_crypt.sha512_crypt("pw", "salt", 10) == sha512_crypt.sha512_crypt(
        "pw", "salt", sha512_crypt.MIN_ROUNDS
    )


def test_generated_salt_uses_crypt_alphabet() -> None:
    salt = sha512_crypt.generate_salt()
    assert len(salt) == sha512_crypt.SALT_LEN
    assert all(ch.encode() in sha512_crypt.ITOA64 for ch in salt)


def test_unicode_password_is_utf8_encoded() -> None:
    assert sha512_crypt.sha512_crypt("비밀번호", "salt") == sha512_crypt.sha512_crypt(
        "비밀번호".encode(), "salt"
    )
