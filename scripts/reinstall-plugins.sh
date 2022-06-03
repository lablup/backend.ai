#! /bin/bash
for repo_path in $(ls -d ./plugins/*/); do
  ./py -m pip install -e "$repo_path"
done
