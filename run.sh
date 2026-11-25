#!/bin/sh
project_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd) || exit 1
export PYTHONPATH="$project_dir${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m src.main "$@"
