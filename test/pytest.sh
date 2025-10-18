#!/usr/bin/env bash

set -eu -o pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="${here}/.."
venv="${here}/.venv"

if [[ ! -d "${venv}" ]]; then
    python3 -m venv "${venv}"
    "${venv}/bin/pip" install pytest==8.4.2
fi

cd "${root}"
PYTHONPATH="${root}" exec "${venv}/bin/pytest" "$@"
