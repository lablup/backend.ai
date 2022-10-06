import os
import re
import sys
import json
import argparse
import tomli as tomllib
from pathlib import Path


def get_config():
    directory = os.path.abspath("./")
    config_path = Path(os.path.join(directory, "pyproject.toml"))

    with open(config_path, "rb") as conf:
        config_toml = tomllib.load(conf)
    config = config_toml["tool"]["towncrier"]
    return config


def get_repository_labels():
    directory = os.path.abspath("./github/workflows")
    config_path = Path(os.path.join(directory, "label-matcher.json"))
    with open(config_path, encoding='utf-8') as json_f:
        labels = [x["name"] for x in json.loads(json_f.read())]
    return labels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-n', '--number', type=int, default=0,
        help='Enter the number of the news fragment you want to create.'
    )
    parser.add_argument(
        '--content', default='',
        help='Enter the contents for the news fragment to modify.'
    )
    parser.add_argument(
        '-f', '--fragment', type=str, default='',
        help='Enter the fragment types for the new fragment you want to modify.'
    )

    args = parser.parse_args()
    if not args.content:
        print("::error ::No contents given from args.")
        sys.exit(1)
    if not args.fragment:
        print("::error ::No fragment types given from args.")
        sys.exit(1)

    repository_labels = get_repository_labels()
    if args.fragment not in repository_labels:
        print(f'Invalid {args.fragment} tag.\nUnable to create/update the news fragment.\n', file=sys.stderr)
        sys.exit(1)

    config = get_config()
    towncrier_types = [t["directory"] for t in config["type"]]
    if args.fragment not in towncrier_types:
        print(f'Towncrier does not support {args.fragment} tag.\n Unable to create/update the news fragment.\n', file=sys.stderr)
        sys.exit(1)

    fragment_dir = config.get("directory")
    try:
        files = os.listdir(fragment_dir)
    except FileNotFoundError as e:
        raise Exception()

    files = [basename for basename in files if len(basename.split(".")) == 3]
    if not files:
        basename = '.'.join([str(0), args.fragment, 'md'])
        output_path = Path(os.path.join(fragment_dir, basename))
        output_path.write_text(args.content)
        print(f'\n### {args.fragment.title()}\n * {args.content} ({basename})', file=sys.stderr)
        print(f'Successfully created the "{args.fragment.title()}" news fragment found by towncrier.\n', file=sys.stderr)
        sys.exit(0)

    for basename in files:
        parts = basename.split(".")
        if parts[1] == args.fragment:
            _basename = basename
            message = f'Successfully updated the "{parts[1].title()}" news fragment found by towncrier.\n'
        else:
            _basename = '.'.join([str(args.number if args.number else 0), args.fragment, 'md'])
            message = f'Successfully created the "{parts[1].title()}" news fragment found by towncrier.\n'
        output_path = Path(os.path.join(fragment_dir, _basename))
        output_path.write_text(args.content)
        print(f'\n### {parts[1].title()}\n * {args.content} ({_basename})', file=sys.stderr)
        print(message, file=sys.stderr)
    sys.exit(0)


if __name__ == '__main__':
    main()
