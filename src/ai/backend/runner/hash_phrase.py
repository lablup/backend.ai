# Based on https://github.com/fpgaminer/hash-phrase/blob/master/hash-phrase.py
# but modified to exclude external pbkdf2 implementation
import binascii
import hashlib
import json
import math
import random
import sys


def pbkdf2_hex(data, salt, iterations, keylen, hashfunc="sha1") -> str:
    dk = hashlib.pbkdf2_hmac(
        hashfunc, bytes(data, "utf-8"), bytes(salt, "utf-8"), iterations, dklen=keylen
    )
    return binascii.hexlify(dk).decode("utf-8")


def load_dictionary(dictionary_file=None) -> list:
    if dictionary_file is None:
        dictionary_file = "/opt/kernel/words.json"

    with open(dictionary_file) as f:
        return json.load(f)


def default_hasher(data) -> str:
    return pbkdf2_hex(data, "", iterations=50000, keylen=32, hashfunc="sha256")


def hash_phrase(
    data,
    minimum_entropy=90,
    dictionary=None,
    hashfunc=default_hasher,
    use_numbers=True,
    separator="",
    capitalize=True,
) -> str:
    if dictionary is None:
        dictionary = load_dictionary()

    dict_len = len(dictionary)
    entropy_per_word = math.log2(dict_len)
    num_words = math.ceil(minimum_entropy / entropy_per_word)

    # Hash the data and convert to a big integer (converts as Big Endian)
    hash = hashfunc(data)
    available_entropy = len(hash) * 4
    hash = int(hash, 16)

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
        remainder = int(hash % dict_len)
        hash = hash / dict_len
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
