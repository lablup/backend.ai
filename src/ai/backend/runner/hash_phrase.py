# Based on https://github.com/fpgaminer/hash-phrase/blob/master/hash-phrase.py
# but modified to exclude external pbkdf2 implementation
from __future__ import annotations

import binascii
import hashlib
import json
import math
import random
import sys
from collections.abc import Callable


def pbkdf2_hex(data: str, salt: str, iterations: int, keylen: int, hashfunc: str = "sha1") -> str:
    dk = hashlib.pbkdf2_hmac(
        hashfunc, bytes(data, "utf-8"), bytes(salt, "utf-8"), iterations, dklen=keylen
    )
    return binascii.hexlify(dk).decode("utf-8")


def load_dictionary(dictionary_file: str | None = None) -> list:
    if dictionary_file is None:
        dictionary_file = "/opt/kernel/words.json"

    with open(dictionary_file) as f:
        return json.load(f)


def default_hasher(data: str) -> str:
    return pbkdf2_hex(data, "", iterations=50000, keylen=32, hashfunc="sha256")


def hash_phrase(
    data: str,
    minimum_entropy: int = 90,
    dictionary: list | None = None,
    hashfunc: Callable[[str], str] = default_hasher,
    use_numbers: bool = True,
    separator: str = "",
    capitalize: bool = True,
) -> str:
    if dictionary is None:
        dictionary = load_dictionary()

    dict_len = len(dictionary)
    entropy_per_word = math.log2(dict_len)
    num_words = math.ceil(minimum_entropy / entropy_per_word)

    # Hash the data and convert to a big integer (converts as Big Endian)
    hash_str = hashfunc(data)
    available_entropy = len(hash_str) * 4
    hash_int = int(hash_str, 16)

    # Check entropy
    if num_words * entropy_per_word > available_entropy:
        raise Exception(
            f"The output entropy of the specified hashfunc ({available_entropy}) is too small."
        )

    # Generate phrase
    phrase = []
    if use_numbers:
        word_idx_to_replace = random.randint(0, num_words)
    else:
        word_idx_to_replace = -1

    for i in range(num_words):
        remainder = int(hash_int % dict_len)
        hash_int = hash_int // dict_len
        if i == word_idx_to_replace:
            phrase.append(str(remainder))
        else:
            phrase.append(dictionary[remainder])

    phrase = [w.lower() for w in phrase]
    if capitalize:
        phrase = [w.capitalize() for w in phrase]
    return separator.join(phrase)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("USAGE: hash-phrase.py DATA")
        sys.exit(-1)

    print(hash_phrase(sys.argv[1]))
