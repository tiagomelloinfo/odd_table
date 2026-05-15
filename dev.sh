#!/usr/bin/env bash
# Dev — roda backend local com --reload + banco separado
set -euo pipefail

cd "$(dirname "$0")"

echo "🔥 Dev: uvicorn na porta 5000 (banco: ./data/dice_roller.db)"
export DATABASE_PATH=./data/dice_roller.db
exec uvicorn app:app --host 0.0.0.0 --port 5000 --reload
