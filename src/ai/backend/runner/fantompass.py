import argparse
import random
import string

import hash_phrase  # pants: no-infer-dep

parser = argparse.ArgumentParser()
parser.add_argument(
    "-c",
    "--clipboard",
    help="Copy password to clipboard rather than displaying it on screen",
    action="store_true",
)
parser.add_argument(
    "-n", "--use-numbers", help="Use numbers in generated passwords", action="store_true"
)
parser.add_argument(
    "--separator",
    help="Separator between the words in the generated password (default: none)",  # NOQA
    default="-",
)
parser.add_argument(
    "--no-capitalize", help="Don't capitalize the words in the password", action="store_true"
)
parser.add_argument(
    "-e",
    "--minimum-entropy",
    help="Minimum entropy for generated passphrase. Doesn't reflect actual password's entropy.",  # NOQA
    default=90,
)
args = parser.parse_args()


if __name__ == "__main__":
    passphrase = "salt"
    host = "main1"
    login = "work"
    modifier = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

    hash = hash_phrase.hash_phrase(
        passphrase + host + login + modifier,
        minimum_entropy=args.minimum_entropy,
        separator=args.separator,
        use_numbers=args.use_numbers,
        capitalize=not args.no_capitalize,
    )

    print(hash)
