#! /bin/bash
# Refer to more details in KB1207
SCIE_PATH=$1
NCE_PYTHON=$(SCIE=inspect "${SCIE_PATH}" | jq -r '.scie.lift.files[] | select(.key == "cpython") | .hash')
NCE_PEX_CLIENT=$(SCIE=inspect "${SCIE_PATH}" | jq -r '.scie.lift.files[] | select(.name | endswith("/pex.pex")) | .hash')
# Referring KB1208, you may need to specify explicit terminfo database locations for scies built using indygreg builds older than 20240224.
# export TERMINFO_DIRS="/etc/terminfo:/lib/terminfo:/usr/share/terminfo"
# Run the Python REPL within the pex evironment
PEX_INTERPRETER=1 ~/.cache/nce/$NCE_PYTHON/cpython*/python/bin/python3 ~/.cache/nce/$NCE_PEX_CLIENT/src.ai.backend*/pex.pex
