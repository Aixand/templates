#!/bin/sh
set -eu
project_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "${AIXAND_DEV_PYTHON:-python3}" -B "$project_root/files/scripts/dev/cli.py" --project "$project_root" "$@"
