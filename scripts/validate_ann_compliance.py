#!/usr/bin/env python3
"""
Validate ANN (flake8-annotations) linter rule compliance.

This script checks if files comply with ANN linter rules by running pants lint
and parsing the output for ANN violations. It's useful for validating batches
of files during incremental linter rule enablement.

Note: This script uses the ANN rules configured in pyproject.toml. To check
specific rules, temporarily modify pyproject.toml to enable only those rules.

Usage:
    python scripts/validate_ann_compliance.py <path>

Examples:
    python scripts/validate_ann_compliance.py src/ai/backend/web/
    python scripts/validate_ann_compliance.py src/ai/backend/common/
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_pants_lint(path: Path) -> tuple[int, str]:
    """Run pants lint and return (return_code, output)."""
    # Global options must come before the goal
    cmd = [
        "pants",
        "--no-colors",
        "--no-dynamic-ui",
        "lint",
        str(path) + "::",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        return (result.returncode, result.stdout + result.stderr)
    except FileNotFoundError:
        print("Error: 'pants' command not found. Make sure Pantsbuild is installed.", file=sys.stderr)
        return (127, "")
    except Exception as e:
        print(f"Error running pants lint: {e}", file=sys.stderr)
        return (1, str(e))


def parse_violations(output: str) -> list[tuple[str, str, str]]:
    """Parse pants lint output to extract ANN violations.

    Returns list of (file, rule, message) tuples.
    """
    violations: list[tuple[str, str, str]] = []

    for line in output.splitlines():
        # Ruff format: path/to/file.py:123:45: ANN001 Message
        if "ANN" in line and ":" in line:
            # Try to parse ruff output format
            parts = line.split(":", maxsplit=3)
            if len(parts) >= 4:
                file_path = parts[0].strip()
                # Extract rule code (ANN001, etc.)
                rule_part = parts[3].strip()
                # Find ANN code
                for word in rule_part.split():
                    if word.startswith("ANN"):
                        rule_code = word
                        message_start = rule_part.find(rule_code) + len(rule_code)
                        message = rule_part[message_start:].strip()
                        violations.append((file_path, rule_code, message))
                        break

    return violations


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate ANN linter rule compliance for Python files"
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Path to Python file or directory to validate",
    )
    args = parser.parse_args()

    # Find project root (directory containing pyproject.toml)
    project_root = Path(__file__).parent.parent.resolve()
    if not (project_root / "pyproject.toml").exists():
        print("Error: Could not find project root (pyproject.toml)", file=sys.stderr)
        return 1

    path = args.path.resolve()
    if not path.exists():
        print(f"Error: {path} does not exist", file=sys.stderr)
        return 1

    try:
        rel_path = path.relative_to(project_root)
    except ValueError:
        print(f"Error: {path} is not under project root", file=sys.stderr)
        return 1

    print(f"Validating: {rel_path}")
    print(f"Running pants lint with configured ANN rules...")
    print()

    return_code, output = run_pants_lint(path)

    # Parse violations
    violations = parse_violations(output)

    if not violations:
        if return_code == 0:
            print("✅ No ANN violations found!")
            return 0
        else:
            # Linting failed but no ANN violations found
            print("⚠️  Linting failed but no ANN violations detected.")
            print("Other linting issues may exist.")
            print()
            print("Lint output:")
            print(output)
            return return_code

    # Display violations
    print(f"❌ Found {len(violations)} ANN violation(s):\n")

    # Group by rule
    by_rule: dict[str, list[tuple[str, str]]] = {}
    for file_path, rule_code, message in violations:
        if rule_code not in by_rule:
            by_rule[rule_code] = []
        by_rule[rule_code].append((file_path, message))

    # Display grouped violations
    for rule_code in sorted(by_rule.keys()):
        rule_violations = by_rule[rule_code]
        print(f"{rule_code}: {len(rule_violations)} violation(s)")
        for file_path, message in rule_violations[:10]:  # Show first 10
            try:
                rel_file = Path(file_path).relative_to(project_root)
            except ValueError:
                rel_file = Path(file_path)
            print(f"  {rel_file}: {message}")
        if len(rule_violations) > 10:
            print(f"  ... and {len(rule_violations) - 10} more")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
