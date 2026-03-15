#!/usr/bin/env bash
set -euo pipefail

# Developer setup script for Ed Insights Platform

GREEN='\033[0;32m'
RED='\033[0;31m'
RESET='\033[0m'

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Checking prerequisites..."

missing=0
for cmd in docker node python3 uv; do
  if command -v "$cmd" >/dev/null 2>&1; then
    version=$("$cmd" --version 2>&1 | head -1)
    printf "  %-10s %s\n" "$cmd" "$version"
  else
    printf "  ${RED}MISSING${RESET}  %s\n" "$cmd"
    ((missing++))
  fi
done

if [ "$missing" -gt 0 ]; then
  echo ""
  echo "Install missing prerequisites before continuing."
  echo "See README.md for details."
  exit 1
fi

echo ""

# Copy .env.example to .env if absent
if [ ! -f "$ROOT/.env" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "Created .env from .env.example — edit it with your credentials."
else
  echo ".env already exists, skipping copy."
fi

echo ""

# Install web dependencies
echo "Installing web dependencies..."
(cd "$ROOT/apps/web" && npm install)

echo ""

# Install API dependencies
echo "Installing API dependencies..."
(cd "$ROOT/apps/api" && uv sync)

echo ""
printf "${GREEN}Setup complete.${RESET} Run ${GREEN}make up${RESET} to start all services.\n"
