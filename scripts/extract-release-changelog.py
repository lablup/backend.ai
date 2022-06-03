import re
import sys
from pathlib import Path


def main():
    input_path = Path('./CHANGELOG.md')
    output_path = Path('./CHANGELOG_RELEASE.md')
    try:
        version = Path('./VERSION').read_text().strip()
        input_text = input_path.read_text()
        m = re.search(rf"(?:^|\n)## {re.escape(version)}(?:[^\n]*)?\n(.*?)(?:\n## |$)", input_text, re.S)
        if m is not None:
            content = m.group(1).strip()
            output_path.write_text(content)
            print(content)
            print("Successfully extracted the latest changelog to CHANGELOG_RELEASE.md", file=sys.stderr)
        else:
            print("::error ::Could not extract the latest changelog from CHANGELOG.md", file=sys.stderr)
            sys.exit(1)
    except IOError as e:
        print(f"::error ::Could read or write from file: {e!r}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
