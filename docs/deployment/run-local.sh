#!/usr/bin/env bash
# Start the stack using locally built images instead of ghcr.io.
cd "$(dirname "$0")"
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build "$@"
