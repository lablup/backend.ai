#! /bin/bash
([ "${READTHEDOCS_VERSION_TYPE}" = "external" ] && curl -sL https://api.github.com/repos/lablup/backend.ai/issues/${READTHEDOCS_VERSION}/labels | jq -e '.[] | select(.name == "area:docs")') && echo "continue" || exit 183
