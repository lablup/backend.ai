#!/bin/sh

TARGET_FILENAME="default-seccomp.json"
TARGET_URL="https://raw.githubusercontent.com/moby/moby/master/profiles/seccomp/default.json"

BASE_PATH=$(cd "$(dirname "$0")"/.. && pwd)

cd $BASE_PATH/src/ai/backend/runner

curl -o "$TARGET_FILENAME" "$TARGET_URL"

if [ $? -eq 0 ]; then
  echo "$TARGET_FILENAME updated successfully."
  exit 0
else
  echo "Failed to download the seccomp profile file. Please check the URL is still valid: $TARGET_URL"
  exit 1
fi
