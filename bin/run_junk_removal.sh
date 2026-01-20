#!/bin/bash
# Wrapper script for remove_junk_tags.py

# Get project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

# Check required variables
if [ -z "$LINKWARDEN_API_URL" ] || [ -z "$LINKWARDEN_TOKEN" ]; then
    echo "Error: LINKWARDEN_API_URL and LINKWARDEN_TOKEN must be set in .env file"
    exit 1
fi

# Run junk tag analyzer
python3 "$PROJECT_ROOT/scripts/remove_junk_tags.py" \
    --api-url "$LINKWARDEN_API_URL" \
    --token "$LINKWARDEN_TOKEN" \
    --blocklist "$PROJECT_ROOT/config/junk_tags_blocklist.txt" \
    "$@"
