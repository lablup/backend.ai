"""Extract one release's changelog block as the GitHub release body.

Everything it needs comes from the arguments: the version names both the
changelog heading to look for and the tag the links point at.

    python scripts/extract-release-changelog.py 26.8.0 --draft
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from changelog_files import changelog_filename

DEFAULT_REPOSITORY = 'lablup/backend.ai'
DEFAULT_OUTPUT = 'CHANGELOG_RELEASE.md'


def release_tag(version):
    """The tag naming a release, derived from its version."""
    return version

def get_prev_tag(tag, repository):
    subprocess.run(['git', 'clone', '--filter=blob:none', '--no-checkout', f'https://github.com/{repository}.git', '.git-tmp'])
    p = subprocess.run(['git', 'describe', '--abbrev=0', '--tags', tag + '^'], capture_output=True, cwd='.git-tmp')
    prev_tag = p.stdout.decode().strip()
    return prev_tag

def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        'version',
        help="The release version, which also names its tag",
    )
    parser.add_argument(
        '--repository', default=DEFAULT_REPOSITORY,
        help=f"The owner/name the release links point at (default: {DEFAULT_REPOSITORY})",
    )
    parser.add_argument(
        '--output', default=DEFAULT_OUTPUT,
        help=f"Where to write the extracted notes (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        '--draft', action='store_true', default=False,
        help="Do not write to file but only print the expected output",
    )
    args = parser.parse_args()

    version = args.version.strip()
    repository = args.repository
    tag = release_tag(version)
    prev_tag = get_prev_tag(tag, repository)
    changelog_name = changelog_filename(version)
    commitlog_url = f"https://github.com/{repository}/compare/{prev_tag}...{tag}"
    changelog_url = f"https://github.com/{repository}/blob/{tag}/{changelog_name}"

    print(f"Making release notes for {tag} ...", file=sys.stderr)

    input_path = Path(f'./{changelog_name}')
    output_path = Path(args.output)
    try:
        input_text = input_path.read_text()
        m = re.search(rf"(?:^|\n)## {re.escape(version)}(?![\w.])(?:[^\n]*)?\n(.*?)(?:\n## |$)", input_text, re.S)
        if m is not None:
            content = m.group(1).strip()
            content += (
                "\n\n### Full Changelog\n\nCheck out [the full changelog](%s) until this release (%s).\n"
                % (changelog_url, tag)
            )
            content += (
                "\n\n### Full Commit Logs\n\nCheck out [the full commit logs](%s) between release (%s) and (%s).\n"
                % (commitlog_url, prev_tag, tag)
            )
            if not args.draft:
                output_path.write_text(content)
            print("--------")
            print(content)
            print("--------")
            print(f"Successfully extracted the latest changelog to {output_path}", file=sys.stderr)
        else:
            print(f"Could not extract the {version} changelog from {changelog_name}", file=sys.stderr)
            sys.exit(1)
    except IOError as e:
        print(f"Could read or write from file: {e!r}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
