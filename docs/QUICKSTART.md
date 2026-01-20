# Quick Start Guide

Get your Linkwarden tags cleaned up in 5 minutes.

## Prerequisites

- Python 3.7+
- Linkwarden instance with API access
- API token with read/write permissions

## Step 1: Install (30 seconds)

```bash
cd linkwarden-cleanup
pip3 install -r requirements.txt
```

## Step 2: Configure (1 minute)

```bash
# Copy environment template
cp .env.example .env

# Edit with your details
nano .env
```

Add your Linkwarden URL and API token:
```bash
LINKWARDEN_API_URL=https://linkwarden.w22.io/api/v1
LINKWARDEN_TOKEN=your_token_here
```

**Get your API token:**
- Log in to Linkwarden
- Settings → API Tokens
- Create new token
- Copy to `.env`

## Step 3: Analyze (1 minute)

```bash
./run_analysis.sh
```

This will:
- Fetch all your tags
- Identify duplicates and issues
- Generate `consolidation_mapping.json`
- Show you a summary report

**Review the output** - it shows what will be changed.

## Step 4: Test Consolidation (1 minute)

```bash
./run_consolidation.sh
```

This runs in **dry-run mode** by default (no changes made). Review the output to see what would change.

## Step 5: Apply Changes (2 minutes)

If the dry-run looks good:

```bash
./run_consolidation.sh --no-dry-run
```

This will:
- Normalize case (music → Music)
- Merge duplicates (AI + ai + ML → AI)
- Delete low-usage tags (<3 uses)

**Watch the progress** and wait for completion.

## Step 6: Set Up Auto-Normalization (Optional)

Prevent future tag proliferation:

```bash
# Test it first
./run_normalization.sh --dry-run

# Set up cron job (runs every 5 minutes)
crontab -e

# Add this line:
*/5 * * * * cd /path/to/linkwarden-cleanup && ./run_normalization.sh >> /var/log/linkwarden-normalize.log 2>&1
```

## Done!

Your tags are now clean and consistent. The normalization service will keep them that way.

## Quick Commands Reference

```bash
# Analyze tags
./run_analysis.sh

# Preview consolidation
./run_consolidation.sh

# Apply consolidation
./run_consolidation.sh --no-dry-run

# Test normalization
./run_normalization.sh --dry-run

# Run normalization
./run_normalization.sh
```

## What Just Happened?

### Before
```
Tags: 4,866
- "Music" (96 uses)
- "music" (34 uses)
- "AI" (91 uses)
- "ai" (2 uses)
- "Machine Learning" (8 uses)
- "ML" (3 uses)
- 3,041 single-use tags
```

### After
```
Tags: ~200
- "Music" (130 uses)
- "AI" (104 uses)
- Single-use tags: deleted
- All tags: consistent case
```

## Troubleshooting

### "Error: API token not found"
→ Did you create `.env` from `.env.example` and add your token?

### "Error: 401 Unauthorized"
→ Check your API token is correct and has the right permissions

### "No recent links found"
→ Normal if you haven't added links recently. The normalizer will catch new ones.

## Next Steps

Read [README.md](README.md) for:
- Detailed configuration options
- Custom semantic groups
- Tuning fuzzy matching
- Advanced usage

## Need Help?

1. Check [README.md](README.md) for detailed docs
2. Review error messages in console output
3. Test with `--dry-run` first
4. Verify your API token permissions
