#!/usr/bin/env bash
set -e

# Load environment configuration inside container
if [ -f "/app/config/boot.env" ]; then
    set -a
    source /app/config/boot.env
    set +a
fi

if [ -f "/app/config/waid.env" ]; then
    set -a
    source /app/config/waid.env
    set +a
fi

echo "=== WAID ARM Container Starting ==="

# Execute scheduler directly with runtime arguments
exec "$@"