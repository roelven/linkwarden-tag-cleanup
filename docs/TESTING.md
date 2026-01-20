# Testing Guide

Comprehensive testing checklist for Linkwarden tag cleanup tools.

## Pre-Testing Setup

### 1. Create Test Environment

```bash
# Set up environment
cp .env.example .env
nano .env  # Add your test instance details
```

### 2. Verify API Access

```bash
# Quick API test
curl -H "Authorization: Bearer YOUR_TOKEN" \
     https://linkwarden.w22.io/api/v1/tags | jq '.[0:3]'
```

Expected: JSON array of tags

## Phase 1: Analysis Testing

### Test 1: Basic Analysis

```bash
./run_analysis.sh
```

**Verify:**
- [ ] Script completes without errors
- [ ] `tags_backup.json` created
- [ ] `consolidation_mapping.json` created
- [ ] Console shows statistics
- [ ] Tag counts match your Linkwarden instance

### Test 2: Check Backup File

```bash
cat tags_backup.json | jq '. | length'
```

**Verify:**
- [ ] Number matches total tags in analysis report
- [ ] File contains valid JSON
- [ ] Each tag has `id`, `name`, and `_count` fields

### Test 3: Review Consolidation Mapping

```bash
cat consolidation_mapping.json | jq '.statistics'
```

**Verify:**
- [ ] `case_normalizations` list makes sense
- [ ] `semantic_consolidations` are appropriate
- [ ] `tags_to_delete` list is reasonable
- [ ] Statistics add up correctly

### Test 4: Manual Mapping Review

```bash
# Check case normalizations
cat consolidation_mapping.json | jq '.case_normalizations' | head -20

# Check semantic consolidations
cat consolidation_mapping.json | jq '.semantic_consolidations'
```

**Verify:**
- [ ] Case changes are correct (Music vs music)
- [ ] Semantic groupings make sense for your use case
- [ ] No important tags marked for deletion

## Phase 2: Consolidation Testing

### Test 5: Dry Run Consolidation

```bash
./run_consolidation.sh
```

**Verify:**
- [ ] All operations show "[DRY RUN]" prefix
- [ ] No actual changes made (check Linkwarden UI)
- [ ] Progress messages are clear
- [ ] Summary statistics shown
- [ ] No errors or warnings

### Test 6: Verify No Changes Made

```bash
# Re-run analysis - counts should be identical
./run_analysis.sh
```

**Verify:**
- [ ] Tag counts unchanged from first analysis
- [ ] No new `tags_backup.json` created (or identical to previous)

### Test 7: Partial Consolidation Test

Test each phase separately:

```bash
# Test only case normalizations
python3 consolidate_tags.py \
    --api-url "$LINKWARDEN_API_URL" \
    --token "$LINKWARDEN_TOKEN" \
    --mapping consolidation_mapping.json \
    --skip-semantic \
    --skip-delete \
    --dry-run
```

**Verify:**
- [ ] Only case normalizations processed
- [ ] Other phases skipped
- [ ] No errors

### Test 8: Apply to Single Tag (Manual)

Manually test renaming one tag:

```bash
# Find a safe tag to test
cat consolidation_mapping.json | jq '.case_normalizations' | head -5

# Pick one and test (replace values):
python3 -c "
import requests
token = 'YOUR_TOKEN'
api = 'https://linkwarden.w22.io/api/v1'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# Fetch tag ID
tags = requests.get(f'{api}/tags', headers=headers).json()
target = [t for t in tags if t['name'] == 'music'][0]
print(f'Tag ID: {target[\"id\"]}')

# Rename to 'Music'
# response = requests.put(f'{api}/tags/{target[\"id\"]}',
#                         headers=headers,
#                         json={'name': 'Music'})
# print(response.status_code, response.json())
"
```

**Verify in Linkwarden UI:**
- [ ] Tag renamed successfully
- [ ] All links still have the tag
- [ ] No duplicates created

## Phase 3: Normalization Testing

### Test 9: Basic Normalization (Dry Run)

```bash
./run_normalization.sh --dry-run
```

**Verify:**
- [ ] Script completes without errors
- [ ] Shows recent links found (or "0 links" if none recent)
- [ ] Tag normalizations shown (if any)
- [ ] Summary statistics displayed

### Test 10: Create Test Link

Add a new link in Linkwarden with intentionally messy tags:
- Tags: `music`, `Technology`, `ai`, `ml`

Then run normalization:

```bash
./run_normalization.sh --dry-run
```

**Verify:**
- [ ] Link detected in recent links
- [ ] Tags normalized:
  - `music` → `Music`
  - `Technology` → `Technology` (already correct)
  - `ai` → `AI`
  - `ml` → `AI` (fuzzy matched)

### Test 11: Fuzzy Matching

```bash
# Test with different thresholds
./run_normalization.sh --similarity-threshold 0.90 --dry-run
./run_normalization.sh --similarity-threshold 0.75 --dry-run
```

**Verify:**
- [ ] Higher threshold (0.90) = fewer matches
- [ ] Lower threshold (0.75) = more matches
- [ ] Matches make sense (not too aggressive)

### Test 12: Lookback Window

```bash
# Process only very recent links
./run_normalization.sh --lookback 5 --dry-run

# Process links from last hour
./run_normalization.sh --lookback 60 --dry-run
```

**Verify:**
- [ ] Shorter lookback = fewer links processed
- [ ] Longer lookback = more links processed

### Test 13: Apply Normalization

After dry-run looks good:

```bash
./run_normalization.sh
```

**Verify in Linkwarden UI:**
- [ ] Test link's tags are normalized
- [ ] No duplicates created
- [ ] Other links unchanged

## Integration Testing

### Test 14: End-to-End Workflow

Full workflow test:

```bash
# 1. Create messy test data in Linkwarden
# Add links with tags: music, Music, AI, ai, ML, machine learning

# 2. Run full cleanup
./run_analysis.sh
./run_consolidation.sh --no-dry-run

# 3. Verify cleanup worked
# Check Linkwarden UI - duplicates should be merged

# 4. Add new messy link
# Tags: tech, technology, dev, developer

# 5. Run normalization
./run_normalization.sh

# 6. Verify normalization worked
# Check new link - tags should be normalized
```

**Verify:**
- [ ] All duplicates merged
- [ ] New tags normalized automatically
- [ ] No data loss
- [ ] Link counts preserved

### Test 15: Stress Test

```bash
# Process many links at once
./run_normalization.sh --lookback 1440 --dry-run  # Last 24 hours
```

**Verify:**
- [ ] Script handles large datasets
- [ ] No memory issues
- [ ] Reasonable execution time
- [ ] Rate limiting prevents API throttling

## Error Testing

### Test 16: Invalid Token

```bash
# Temporarily break token in .env
sed -i.bak 's/LINKWARDEN_TOKEN=.*/LINKWARDEN_TOKEN=invalid/' .env

./run_analysis.sh
```

**Verify:**
- [ ] Clear error message about authentication
- [ ] Script exits gracefully
- [ ] No partial/corrupt files created

```bash
# Restore token
mv .env.bak .env
```

### Test 17: Network Issues

```bash
# Invalid API URL
python3 analyze_tags.py \
    --api-url https://invalid-url.example.com/api/v1 \
    --token "$LINKWARDEN_TOKEN"
```

**Verify:**
- [ ] Clear error about connection failure
- [ ] Script exits gracefully
- [ ] Helpful error message

### Test 18: Missing Files

```bash
# Try consolidation without mapping file
rm consolidation_mapping.json
./run_consolidation.sh
```

**Verify:**
- [ ] Clear error about missing file
- [ ] Script exits gracefully

## Performance Testing

### Test 19: Timing

```bash
time ./run_analysis.sh
time ./run_normalization.sh --dry-run
```

**Verify:**
- [ ] Analysis completes in reasonable time
- [ ] Normalization completes in reasonable time
- [ ] No timeouts or hangs

### Test 20: Rate Limiting

Monitor API calls:

```bash
# Run with verbose output
python3 normalize_new_tags.py \
    --api-url "$LINKWARDEN_API_URL" \
    --token "$LINKWARDEN_TOKEN" \
    --lookback 60 \
    --dry-run 2>&1 | grep -i "rate\|limit\|429"
```

**Verify:**
- [ ] No rate limit errors (429)
- [ ] Scripts include delays between calls
- [ ] API remains responsive

## Automated Testing

### Test 21: Cron Setup

```bash
# Add test cron job
(crontab -l 2>/dev/null; echo "*/30 * * * * cd /path/to/linkwarden-cleanup && ./run_normalization.sh >> /tmp/test-normalize.log 2>&1") | crontab -

# Wait 30 minutes, then check
cat /tmp/test-normalize.log
```

**Verify:**
- [ ] Cron job runs successfully
- [ ] Log file created
- [ ] No errors in log
- [ ] Can see multiple runs

```bash
# Remove test cron
crontab -l | grep -v "linkwarden-cleanup" | crontab -
```

## Rollback Testing

### Test 22: Backup Restoration

If something goes wrong:

```bash
# You should have tags_backup.json from analysis

# Manually restore a tag using backup
python3 -c "
import json
with open('tags_backup.json') as f:
    backup = json.load(f)
    # Review backup and restore specific tags if needed
    print(f'Backup contains {len(backup)} tags')
    print('First tag:', backup[0])
"
```

**Verify:**
- [ ] Backup file is complete
- [ ] Contains all original tag data
- [ ] Can be used to restore if needed

## Final Verification

### Test 23: Data Integrity

After all tests:

```bash
# Re-run analysis
./run_analysis.sh

# Compare with original backup
python3 -c "
import json
with open('tags_backup.json') as f:
    original = json.load(f)
with open('tags_backup.json') as f:
    current = json.load(f)

print(f'Original tags: {len(original)}')
print(f'Current tags: {len(current)}')
print(f'Difference: {len(original) - len(current)}')
"
```

**Verify:**
- [ ] Tag reduction matches expectations
- [ ] No unexpected data loss
- [ ] All links still accessible
- [ ] Tags make sense in Linkwarden UI

## Test Checklist Summary

- [ ] All Phase 1 tests pass (Analysis)
- [ ] All Phase 2 tests pass (Consolidation)
- [ ] All Phase 3 tests pass (Normalization)
- [ ] Integration tests pass
- [ ] Error handling tests pass
- [ ] Performance acceptable
- [ ] Backups working
- [ ] Ready for production use

## Common Issues & Solutions

### Issue: "Tag not found"
**Solution:** Tag already deleted/renamed. Re-run analysis to regenerate mapping.

### Issue: Slow performance
**Solution:** Increase rate limiting delays in scripts (edit `time.sleep()` values).

### Issue: API timeouts
**Solution:** Check network connection, Linkwarden instance health.

### Issue: Unexpected merges
**Solution:** Lower similarity threshold or adjust semantic groups in code.

## Production Deployment Checklist

Before deploying to production:

- [ ] All tests passed
- [ ] Backups verified
- [ ] Dry runs look good
- [ ] API token has correct permissions
- [ ] Cron job configured correctly
- [ ] Logs directory exists and writable
- [ ] Monitoring in place
- [ ] Rollback plan documented

## Support

If tests fail:
1. Check error messages carefully
2. Verify API credentials
3. Test with smaller datasets first
4. Review script source code
5. Check Linkwarden API documentation
