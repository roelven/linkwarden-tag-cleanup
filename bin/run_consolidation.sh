#!/bin/bash
# Wrapper script for consolidate_tags.py

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

# Check if --no-dry-run flag is present
DRY_RUN="--dry-run"
EXTRA_ARGS=()

for arg in "$@"; do
    if [ "$arg" = "--no-dry-run" ]; then
        DRY_RUN=""
    else
        EXTRA_ARGS+=("$arg")
    fi
done

# Run consolidation (dry-run by default for safety)
python3 "$PROJECT_ROOT/scripts/consolidate_tags.py" \
    --api-url "$LINKWARDEN_API_URL" \
    --token "$LINKWARDEN_TOKEN" \
    --mapping "$PROJECT_ROOT/consolidation_mapping.json" \
    $DRY_RUN \
    "${EXTRA_ARGS[@]}"

# Show appropriate message based on mode
if [ -n "$DRY_RUN" ]; then
    echo ""
    echo "NOTE: This was a dry-run. To apply changes, run:"
    echo "  bin/run_consolidation.sh --no-dry-run"
fi
