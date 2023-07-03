#! /bin/bash
# This script is executed inside the RTD's build environment.
wget -qO ./jq https://github.com/jqlang/jq/releases/download/jq-1.6/jq-linux64
chmod +x ./jq
([ "${READTHEDOCS_VERSION_TYPE}" = "external" ] && curl -sL https://api.github.com/repos/lablup/backend.ai/issues/${READTHEDOCS_VERSION}/labels | ./jq -e '.[] | select(.name == "area:docs")' > /dev/null) && echo "continue" || exit 183
