#!/usr/bin/env python
import json
import os
import re
import sys
from pathlib import Path

import tomlkit


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

    files = [f.name for f in base_path.iterdir() if f.is_file()]
    existing_fragments = []
    for file in files:
        if file[0 : file.find(".")] == pr_number:
            existing_fragments.append(file)
    if existing_fragments:
        print(f"The news fragment(s) for the PR #{pr_number} already exists:")
        for file in existing_fragments:
            print(file)
        with open(os.getenv("GITHUB_OUTPUT", os.devnull), "a") as ghoutput:
            print("has_renamed_pairs=false", file=ghoutput)
        sys.exit(0)

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
    else:
        print("There are no unnumbered news fragments.")
        with open(os.getenv("GITHUB_OUTPUT", os.devnull), "a") as ghoutput:
            print("has_renamed_pairs=false", file=ghoutput)
    sys.exit(0)


if __name__ == "__main__":
    pr_number = sys.argv[1]
    main(pr_number)
