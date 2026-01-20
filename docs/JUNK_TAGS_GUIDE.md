# Junk Tag Removal Guide

Remove non-substantive tags that don't provide meaningful categorization.

## What Are Junk Tags?

Tags that are too generic or vague to be useful for organizing links:
- **Common verbs**: "avoid", "feel", "sign", "read", "view"
- **Generic nouns**: "thing", "stuff", "room", "place"
- **UI elements**: "sign up", "login", "click here", "more"
- **Vague words**: "men", "women", "sea", "land"
- **Articles/prepositions**: "a", "the", "and", "of"
- **Single characters**: "a", "1", "x"

## Quick Start

### 1. Analyze What Would Be Removed

```bash
./run_junk_removal.sh --analyze
```

This shows:
- How many junk tags were found
- Breakdown by reason (blocklist, too_short, etc.)
- Sample tags that would be removed
- Total link references affected

### 2. Review and Customize Blocklist

Edit `junk_tags_blocklist.txt` to add your own junk tags:

```bash
nano junk_tags_blocklist.txt
```

Add one tag per line:
```
# My custom junk tags
foo
bar
test
placeholder
```

### 3. Export for Review

```bash
./run_junk_removal.sh --analyze --export junk_tags_found.json
```

Review `junk_tags_found.json` to see exactly what will be removed.

### 4. Remove Junk Tags (Dry Run)

```bash
./run_junk_removal.sh --dry-run
```

Preview the removal without making changes.

### 5. Actually Remove Them

```bash
./run_junk_removal.sh
```

Confirm when prompted to delete the junk tags.

## Detection Algorithms

The script identifies junk tags using multiple strategies:

### 1. Blocklist Matching
- Checks against built-in list of ~200 common junk words
- Loads additional words from `junk_tags_blocklist.txt`
- Case-insensitive matching

### 2. Length-Based Rules
- Tags ≤2 characters (unless UPPERCASE acronyms)
- Single character tags
- Examples: "a", "to", "in"

### 3. Pattern-Based Rules
- All digits: "123", "2024"
- No alphanumeric characters: "...", "---"
- Generic suffixes on short words: "going", "done", "doing"

### 4. Acronym Protection
Known valid acronyms are preserved:
- Technology: AI, ML, API, URL, CSS, HTML, JS, SQL
- Cloud: AWS, GCP, IoT, VPN, CDN
- Business: CEO, CTO, HR, PR, CRM, ERP
- Format: JSON, XML, PDF, REST

## Advanced Options

### Delete Only Low-Usage Junk Tags

Only remove junk tags used on ≤5 links:

```bash
./run_junk_removal.sh --min-usage 5
```

This is safer - keeps junk tags that are heavily used (might be intentional).

### Use Custom Blocklist

```bash
python3 remove_junk_tags.py \
    --api-url "$LINKWARDEN_API_URL" \
    --token "$LINKWARDEN_TOKEN" \
    --blocklist my_custom_blocklist.txt \
    --analyze
```

### Export Analysis Results

```bash
./run_junk_removal.sh --analyze --export junk_analysis.json
```

Creates JSON file with:
- Tag name, ID, usage count
- Reason for classification as junk
- Can be reviewed or used for custom processing

## Examples

### Example 1: Conservative Cleanup

Only remove junk tags with 0 uses:

```bash
./run_junk_removal.sh --min-usage 0
```

### Example 2: Review Before Deleting

```bash
# 1. Analyze and export
./run_junk_removal.sh --analyze --export review.json

# 2. Review the file
cat review.json | jq '.junk_tags[] | select(.usage > 10)'

# 3. Remove only low-usage ones
./run_junk_removal.sh --min-usage 3
```

### Example 3: Add Custom Junk Tags

```bash
# Add to blocklist
echo "placeholder" >> junk_tags_blocklist.txt
echo "example" >> junk_tags_blocklist.txt
echo "demo" >> junk_tags_blocklist.txt

# Analyze with updated blocklist
./run_junk_removal.sh --analyze
```

## Built-in Junk Word Categories

### Common Verbs (~50 words)
avoid, feel, sign, read, view, click, get, make, see, go, come, take, give, find, use, tell, ask, work, seem, try, leave, call, keep, let, begin, help, show, hear, play, run, move, live, believe, bring, happen, write, sit, stand, lose, pay, meet, include

### Generic Nouns (~30 words)
thing, stuff, item, place, time, way, room, area, part, case, point, group, number, fact, hand, eye, side, head, house, service, system, program, question, work, problem, level, form, kind, type, sort

### Generic Adjectives (~30 words)
good, bad, new, old, great, small, large, big, little, high, low, long, short, different, same, important, public, able, own, other, early, young, few, next, last, right, left, sure, best, better, worse, worst

### Articles/Prepositions/Conjunctions (~40 words)
a, an, the, and, or, but, if, because, as, until, while, of, at, by, for, with, about, against, between, into, through, during, before, after, above, below, to, from, up, down, in, out, on, off, over, under, again

### Pronouns (~20 words)
i, you, he, she, it, we, they, them, their, this, that, these, those, who, which, what, where, when, why, how, all, each, every, both, some, any, many, much

### UI/Navigation (~15 words)
signup, sign up, login, log in, logout, sign in, click here, more, less, back, next, previous, home, menu, search, subscribe, follow, share, like, comment, save, delete

### Vague Descriptors (~20 words)
men, women, people, person, man, woman, child, children, sea, land, water, air, fire, earth, sun, moon, day, night, week, month, year, morning, evening, afternoon

## Statistics from Analysis

Typical results on LLM-tagged instances:

**Before:**
- Total tags: 4,866
- Junk tags: ~800-1,200 (16-25%)
- Examples: "Avoid", "Sign Up", "Room", "Feel", "sea", "men"

**After:**
- Total tags: ~3,700-4,100
- Reduction: 15-25%
- Cleaner, more meaningful tag set

## Safety Features

1. **Dry-run by default**: Must confirm before deletion
2. **Acronym protection**: Valid tech acronyms preserved
3. **Usage threshold**: Can limit to low-usage tags only
4. **Export capability**: Review before deleting
5. **No link deletion**: Only tags are removed, links keep other tags

## Customization

### Add Your Own Detection Logic

Edit `remove_junk_tags.py` and modify `is_junk_tag()` method:

```python
def is_junk_tag(self, tag_name: str) -> tuple[bool, str]:
    lower_name = tag_name.lower().strip()

    # Add custom rule
    if lower_name.startswith('temp_'):
        return True, "temp_prefix"

    # ... existing rules ...
```

### Add More Valid Acronyms

Edit the `VALID_ACRONYMS` set in the script:

```python
VALID_ACRONYMS = {
    'ai', 'ml', 'api',
    # Add yours:
    'myorg', 'myproduct', 'custom',
}
```

## Troubleshooting

### Too Many False Positives

If good tags are being marked as junk:

1. Check if they're in the blocklist
2. Add them to `VALID_ACRONYMS` in the script
3. Use `--min-usage` to protect heavily-used tags

### Too Few Detected

If obvious junk tags aren't detected:

1. Add them to `junk_tags_blocklist.txt`
2. Extend the detection logic in `is_junk_tag()`

### Want to Undo

Unfortunately, deleted tags can't be easily restored. Best practices:

1. **Always** run `--analyze` first
2. **Always** use `--dry-run` before actual removal
3. **Consider** using `--min-usage` for safer cleanup
4. **Export** the junk list before deleting

## Integration with Tag Normalization

After removing junk tags, update your normalization service:

1. Add junk words to normalization blocklist
2. Prevent LLM from generating these tags
3. Update `normalize_new_tags.py` to skip junk words

## Command Reference

```bash
# Analyze only
./run_junk_removal.sh --analyze

# Export junk list
./run_junk_removal.sh --analyze --export junk.json

# Dry run
./run_junk_removal.sh --dry-run

# Delete all junk tags
./run_junk_removal.sh

# Delete only low-usage junk tags
./run_junk_removal.sh --min-usage 3

# Use custom blocklist
python3 remove_junk_tags.py \
    --api-url URL --token TOKEN \
    --blocklist custom.txt \
    --analyze
```

## Best Practices

1. **Review first**: Always analyze before removing
2. **Start conservative**: Use `--min-usage` initially
3. **Customize blocklist**: Add domain-specific junk tags
4. **Run periodically**: Monthly cleanup recommended
5. **After LLM tagging**: Run after bulk auto-tagging sessions

## Related Tools

- `analyze_tags.py` - Find duplicate/overlapping tags
- `consolidate_tags.py` - Merge similar tags
- `normalize_new_tags.py` - Prevent future junk tags

## Support

If a good tag is incorrectly classified as junk:
1. Remove it from `junk_tags_blocklist.txt`
2. Add it to `VALID_ACRONYMS` in the script
3. Adjust detection rules in `is_junk_tag()` method
