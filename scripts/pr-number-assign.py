#!/usr/bin/env python
import json
import os
import re
import sys
from pathlib import Path

import tomlkit

exempted_files = ["README.md", "template.md"]

def read_news_types() -> set[str]:
    with open("./pyproject.toml", "r") as f:
        data = tomlkit.load(f)
        news_types = {section["directory"] for section in data["tool"]["towncrier"]["type"]}
    return news_types


def main(pr_number: str) -> None:
    news_types = read_news_types()
    base_path = Path("./changes")
    rx_unnumbered_fragment = re.compile(
        r"^(\.)?(?P<type>" + "|".join(map(re.escape, news_types)) + r")(\.)?(md)?$"
    )
    rx_numbered_fragment = re.compile(
        r"^\d+\.(?P<type>" + "|".join(map(re.escape, news_types)) + r")(\.)?(md)?$"
    )

    files = [f.name for f in base_path.iterdir() if f.is_file() and f.name not in exempted_files]
    existing_fragments = []
    for file in files:
        if rx_numbered_fragment.search(file):
            if file[0 : file.find(".")] == pr_number:
                existing_fragments.append(file)
        elif rx_unnumbered_fragment.search(file) is None:
            print(f"{file} is an invalid news fragment filename.")
            sys.exit(1)

    renamed_pairs = []
    for file in files:
        if match := rx_unnumbered_fragment.search(file):
            original_filename = match.group()
            news_type = match.group("type")
            numbered_filename = f"{pr_number}.{news_type}.md"
            file_path = base_path / original_filename
            file_path.rename(base_path / numbered_filename)
            print(f"{original_filename} is renamed to {pr_number}.{news_type}.md")
            renamed_pairs.append(
                (original_filename, numbered_filename),
            )

    if renamed_pairs:
        with open(os.getenv("GITHUB_OUTPUT", os.devnull), "a") as ghoutput:
            rename_results = [f"{pair[0]} -> {pair[1]}" for pair in renamed_pairs]
            print(f"rename_results={json.dumps(rename_results)}", file=ghoutput)
            print("has_renamed_pairs=true", file=ghoutput)
    elif existing_fragments:
        print(f"The news fragment(s) for the PR #{pr_number} already exists:")
        for file in existing_fragments:
            print(file)
        with open(os.getenv("GITHUB_OUTPUT", os.devnull), "a") as ghoutput:
            print("has_renamed_pairs=false", file=ghoutput)
    else:
        print("There are no unnumbered news fragments.")
        with open(os.getenv("GITHUB_OUTPUT", os.devnull), "a") as ghoutput:
            print("has_renamed_pairs=false", file=ghoutput)
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <PR Number>")
        sys.exit(1)
    pr_number = sys.argv[1]
    main(pr_number)
