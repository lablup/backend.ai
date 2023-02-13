#!/usr/bin/env python
import os
import re
from pathlib import Path

import tomlkit

pr_number = args[1]
path = Path("./changes")

with open("./pyproject.toml", "r") as f:
    data = tomlkit.load(f)
    t_types = [sub["directory"] for sub in data["tool"]["towncrier"]["type"]]

pattern = r"^(\.)?(" + "|".join(t_types) + ")(\.)?(md)?$"
result = None

files = [f.name for f in path.iterdir() if f.is_file()]
print(str(files) + " are in changes floder.")

for file in files:
    if str(file[0 : file.find(".")]) == pr_number:
        print("Change log file already exist for this PR.")
        exit(0)

for file in files:
    result = re.search(pattern, file)
    if result:
        original_filename = result.group()
        feat = re.search(r"|".join(t_types), original_filename).group()
        file_path = path / original_filename
        file_path.rename(path / (pr_number + "." + feat + ".md"))

        env_file = os.getenv("GITHUB_ENV")
        myfile = open(env_file, "a")
        myfile.write("ORIGINAL_FILENAME=" + original_filename + "\n")
        myfile.write("FEAT=" + feat)
        myfile.close()

        print(original_filename + " file changed to " + pr_number + "." + feat + ".md")
        exit(0)

if result:
    print("There is not change log file for this PR in changes folder.")
    print("Also, there is not feature named file in changes folder.")
    exit(0)
