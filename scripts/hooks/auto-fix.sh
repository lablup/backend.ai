#!/bin/bash
# Claude Code Stop hook: Auto-fix Python files after Claude finishes responding
# Runs pants fix on all Python files modified during the conversation

set -e

# Parse JSON input from stdin
INPUT=$(cat)

# Change to project directory
cd "${CLAUDE_PROJECT_DIR:-.}"

# Get list of modified files from git
MODIFIED_FILES=$(git diff --name-only HEAD 2>/dev/null | grep '\.py$' || true)

# If no Python files modified, exit
if [ -z "$MODIFIED_FILES" ]; then
    exit 0
fi

# Run pants fix on all modified Python files
echo "Auto-fixing modified Python files..." >&2
if pants fix $MODIFIED_FILES 2>/dev/null; then
    echo "✓ Auto-fix applied to modified files" >&2
else
    # Don't fail the hook if fix fails
    echo "⚠ Auto-fix failed (non-blocking)" >&2
fi

exit 0
