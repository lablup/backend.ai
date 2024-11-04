#!/bin/sh

TARGET_PATH="src/ai/backend/runner/default-seccomp.json"
TARGET_URL="https://raw.githubusercontent.com/moby/moby/master/profiles/seccomp/default.json"

curl -o "$TARGET_PATH" "$TARGET_URL"

if [ $? -eq 0 ]; then
  echo "$TARGET_PATH updated successfully."
else
  echo "Failed to download the seccomp profile file. Please check the URL is still valid: $TARGET_URL"
fi
