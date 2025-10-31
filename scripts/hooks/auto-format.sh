#!/bin/bash
# Claude Code PostToolUse hook: Auto-format Python files after Edit/Write
# Receives JSON via stdin containing tool execution context

set -e

# Parse JSON input from stdin
INPUT=$(cat)

# Extract file path from tool_input
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# If no file path, exit
if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Only process Python files
if [[ ! "$FILE_PATH" == *.py ]]; then
    exit 0
fi

# Change to project directory
cd "${CLAUDE_PROJECT_DIR:-.}"

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

# Auto-format the file using pants
# Note: We only run 'pants fmt' here, not 'pants fix'
# Reason: 'pants fix' might remove imports before they're used in subsequent edits
# 'pants fix' runs in Git pre-commit hook instead
echo "Auto-formatting: $FILE_PATH" >&2

if pants fmt "$FILE_PATH" 2>/dev/null; then
    echo "✓ Formatting applied" >&2
else
    echo "⚠ Formatting failed (non-blocking)" >&2
fi

exit 0
