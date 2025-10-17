#!/usr/bin/env bash

here="$(builtin cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH=$here python3 -m graphite_shim