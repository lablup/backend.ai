#!/bin/bash
# This code exports every pants data for development-related tools
pants export --resolve=python-default --resolve=python-kernel --resolve=pants-plugins --resolve=black --resolve=ruff --resolve=pytest --resolve=coverage-py --resolve=mypy --resolve=towncrier
