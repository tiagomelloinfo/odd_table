#!/usr/bin/env bash
# Dev — roda backend local com banco separado do prod
set -euo pipefail

cd "$(dirname "$0")"
DATABASE_PATH=./data/dice_roller.db uvicorn app:app --host 0.0.0.0 --port 5000 --reload
