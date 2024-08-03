#!/bin/bash
paths=$(cat scripts/agent/list-of-legacy-krunner-files.txt)
cd src/ai/backend/runner
for path in $paths; do
  name=$(basename $path)
  target_name=$(echo $name | sed -E 's/\.(ubuntu|alpine|centos)[0-9]+\.[0-9]+//g')
  echo "copying $name to $target_name"
  # ln -s $target_name $name
  cp "$target_name" "$name"
done
