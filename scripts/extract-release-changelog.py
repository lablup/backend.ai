import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from changelog_files import changelog_filename

DEFAULT_REPOSITORY = 'lablup/backend.ai'


def get_repository():
    return os.environ.get('GITHUB_REPOSITORY', DEFAULT_REPOSITORY)

def get_tag():
    gh_ref_name = os.environ.get('GITHUB_REF_NAME')
    if gh_ref_name:
        return gh_ref_name
    p = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True)
    revision = p.stdout.decode().strip()
    return revision

def get_prev_tag():
    tag = get_tag()
    subprocess.run(['git', 'clone', '--filter=blob:none', '--no-checkout', f'https://github.com/{get_repository()}.git', '.git-tmp'])
    p = subprocess.run(['git', 'describe', '--abbrev=0', '--tags', tag + '^'], capture_output=True, cwd='.git-tmp')
    prev_tag = p.stdout.decode().strip()
    return prev_tag

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--draft', action='store_true', default=False,
        help="Do not write to file but only print the expected output",
    )
    args = parser.parse_args()

    prev_tag, tag = get_prev_tag(), get_tag()
    repository = get_repository()
    version = Path('./VERSION').read_text().strip()
    changelog_name = changelog_filename(version)
    commitlog_url = f"https://github.com/{repository}/compare/{prev_tag}...{tag}"
    changelog_url = f"https://github.com/{repository}/blob/{tag}/{changelog_name}"

    print(f"Making release notes for {tag} ...", file=sys.stderr)

    input_path = Path(f'./{changelog_name}')
    output_path = Path('./CHANGELOG_RELEASE.md')
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
            print("Successfully extracted the latest changelog to CHANGELOG_RELEASE.md", file=sys.stderr)
        else:
            print(f"::error ::Could not extract the {version} changelog from {changelog_name}", file=sys.stderr)
            sys.exit(1)
    except IOError as e:
        print(f"::error ::Could read or write from file: {e!r}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
