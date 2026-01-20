# Linkwarden Tag Cleanup Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

Complete toolkit for cleaning up and maintaining consistent tags in [Linkwarden](https://linkwarden.app) instances, especially those using LLM-based auto-tagging.

## Problem

Auto-tagging with small LLMs (like gemma3b) creates severe tag inconsistencies:

- **Case duplicates**: "Music" vs "music", "AI" vs "ai" (43 found)
- **Semantic overlaps**: "AI", "Machine Learning", "ML", "LLM" all meaning similar things
- **Tag proliferation**: 84% of tags used on ≤3 links
- **Junk tags**: Non-substantive tags like "Avoid", "Sign Up", "Room", "Feel"
- **No reuse**: LLM creates new tags instead of reusing existing ones

**Result**: 4,866 tags where only ~200 are actually useful.

## Solution

This toolkit provides four complementary tools:

1. **Tag Analyzer** - Identify duplicates, overlaps, and low-usage tags
2. **Tag Consolidator** - Merge duplicates and clean up existing tags
3. **Tag Normalizer** - Prevent future tag proliferation (ongoing service)
4. **Junk Remover** - Remove non-substantive tags that provide no value

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/roelven/linkwarden-tag-cleanup.git
cd linkwarden-tag-cleanup

# Install dependencies
pip3 install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Add your Linkwarden API URL and token
```

### Basic Usage

```bash
# 1. Analyze your tags
bin/run_analysis.sh

# 2. Consolidate duplicates (dry-run first)
bin/run_consolidation.sh
bin/run_consolidation.sh --no-dry-run

# 3. Remove junk tags
bin/run_junk_removal.sh --analyze
bin/run_junk_removal.sh

# 4. Set up ongoing normalization (cron)
crontab -e
# Add: */5 * * * * cd /path/to/linkwarden-cleanup && bin/run_normalization.sh >> normalization.log 2>&1
```

See [QUICKSTART.md](docs/QUICKSTART.md) for detailed setup instructions.

## Features

### Tag Analysis
- ✅ Identify case-insensitive duplicates
- ✅ Find semantic overlaps
- ✅ Detect low-usage tags
- ✅ Generate consolidation mappings
- ✅ Automatic backup before changes

### Tag Consolidation
- ✅ Merge case variants (music → Music)
- ✅ Merge semantic duplicates (AI/ML/LLM → AI)
- ✅ Delete low-usage tags (<3 uses)
- ✅ Update all affected links
- ✅ Dry-run mode for safety

### Tag Normalization (Ongoing)
- ✅ Fuzzy matching (85% similarity)
- ✅ Automatic case normalization
- ✅ Reuse existing tags
- ✅ Runs via cron/systemd
- ✅ Configurable thresholds

### Junk Tag Removal
- ✅ Remove non-substantive tags
- ✅ 200+ built-in junk patterns
- ✅ Custom blocklist support
- ✅ Smart acronym detection
- ✅ Usage-based filtering

## Project Structure

```
linkwarden-cleanup/
├── bin/                    # Wrapper scripts (run these)
│   ├── run_analysis.sh
│   ├── run_consolidation.sh
│   ├── run_normalization.sh
│   └── run_junk_removal.sh
├── scripts/                # Core Python scripts
│   ├── analyze_tags.py
│   ├── consolidate_tags.py
│   ├── normalize_new_tags.py
│   └── remove_junk_tags.py
├── config/                 # Configuration files
│   ├── config.example.json
│   └── junk_tags_blocklist.txt
├── docs/                   # Documentation
│   ├── QUICKSTART.md
│   ├── JUNK_TAGS_GUIDE.md
│   ├── TESTING.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── deployment/         # Systemd setup
└── examples/               # Example configs and debug scripts
```

## Expected Results

### Before Cleanup
- **Total tags**: 4,866
- **Single-use**: 3,041 (62.5%)
- **Low-use (≤3)**: 4,089 (84%)
- **Junk tags**: ~1,000
- **Average usage**: 1.5 links/tag

### After Cleanup
- **Total tags**: 150-250
- **Tag reduction**: 85%
- **Case consistency**: 100%
- **Average usage**: 15+ links/tag
- **Ongoing prevention**: 80-90% of future duplicates

## Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get up and running in 5 minutes
- **[Junk Tags Guide](docs/JUNK_TAGS_GUIDE.md)** - Remove non-substantive tags
- **[Testing Guide](docs/TESTING.md)** - Comprehensive test suite
- **[Deployment Guide](docs/deployment/INSTALL.md)** - Systemd setup

## Configuration

### Environment Variables (.env)

```bash
LINKWARDEN_API_URL=https://your-linkwarden.example.com/api/v1
LINKWARDEN_TOKEN=your_api_token_here
LOW_USE_THRESHOLD=3
SIMILARITY_THRESHOLD=0.85
LOOKBACK_MINUTES=15
```

### Get Your API Token

1. Log in to Linkwarden
2. Go to Settings → API Tokens
3. Create new token with read/write permissions
4. Copy token to `.env` file

## Advanced Usage

### Custom Tag Consolidations

Edit the consolidation mapping before applying:

```bash
bin/run_analysis.sh
nano consolidation_mapping.json  # Review and customize
bin/run_consolidation.sh --no-dry-run
```

### Custom Junk Tag Blocklist

Add your own junk tags:

```bash
echo "placeholder" >> config/junk_tags_blocklist.txt
echo "example" >> config/junk_tags_blocklist.txt
bin/run_junk_removal.sh --analyze
```

### Partial Consolidation

```bash
# Only case normalizations
python3 scripts/consolidate_tags.py --skip-semantic --skip-delete

# Only semantic consolidations
python3 scripts/consolidate_tags.py --skip-case --skip-delete
```

## Requirements

- Python 3.7+
- `requests` library
- Linkwarden instance with API access
- API token with read/write permissions

## Safety Features

1. **Automatic backups** - Tags saved before changes
2. **Dry-run mode** - Preview changes before applying
3. **Confirmation prompts** - Prevents accidental deletions
4. **Rate limiting** - Avoids API throttling
5. **Error handling** - Graceful failure recovery

## Troubleshooting

### Authentication Errors

```bash
# Verify your token works
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://your-linkwarden.example.com/api/v1/tags
```

### No Recent Links Found

Normal if no links were recently added. The normalization service will catch new links on the next run.

### Tag Not Found Errors

Tag was already deleted or renamed. Safe to ignore.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

Created to solve tag proliferation issues with LLM-based auto-tagging in Linkwarden.

## Related Projects

- [Linkwarden](https://github.com/linkwarden/linkwarden) - Self-hosted bookmark manager
- [Linkwarden Docs](https://docs.linkwarden.app) - Official documentation

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check the [documentation](docs/)
- Review the [testing guide](docs/TESTING.md)

---

**Note**: This toolkit works with Linkwarden v2.x. Always backup your data before running cleanup operations.
