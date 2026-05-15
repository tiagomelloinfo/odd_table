#!/usr/bin/env bash
# Prod — sobe Docker Compose com Cloudflare Tunnel pra jogar
# Banco fica no volume Docker (/data/dice_roller.db)
set -euo pipefail

cd "$(dirname "$0")"

echo "🎲 Prod: docker compose up (banco: volume Docker /data/dice_roller.db)"
echo "   Acessar: http://localhost:8080"
exec docker compose up
