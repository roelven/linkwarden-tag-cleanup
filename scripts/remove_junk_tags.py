#!/usr/bin/env python3
"""
Remove Non-Substantive Tags from Linkwarden

Identifies and removes "junk" tags that don't provide meaningful categorization:
- Common verbs (avoid, feel, sign, etc.)
- Generic words (room, thing, stuff)
- Articles, prepositions, conjunctions
- Very short words (<3 chars) unless they're acronyms
- Single-word vague tags

Usage:
    # Analyze what would be removed
    python3 remove_junk_tags.py --api-url URL --token TOKEN --analyze

    # Remove junk tags (dry-run)
    python3 remove_junk_tags.py --api-url URL --token TOKEN --dry-run

    # Actually remove them
    python3 remove_junk_tags.py --api-url URL --token TOKEN
"""

import argparse
import json
import sys
import time
from typing import Dict, List, Set
import requests


class JunkTagRemover:
    # Curated list of non-substantive words that shouldn't be tags
    JUNK_WORDS = {
        # Common verbs
        'avoid', 'feel', 'sign', 'read', 'view', 'click', 'get', 'make', 'see',
        'go', 'come', 'take', 'give', 'find', 'use', 'tell', 'ask', 'work',
        'seem', 'try', 'leave', 'call', 'keep', 'let', 'begin', 'help',
        'show', 'hear', 'run', 'move', 'live', 'believe', 'bring',
        'happen', 'write', 'sit', 'stand', 'lose', 'pay', 'meet', 'include',

        # Generic nouns
        'thing', 'stuff', 'item', 'place', 'time', 'way', 'room', 'area',
        'part', 'case', 'point', 'group', 'number', 'fact', 'hand', 'eye',
        'side', 'head', 'house', 'service', 'program', 'question',
        'work', 'problem', 'level', 'form', 'kind', 'type', 'sort',

        # Generic adjectives
        'good', 'bad', 'new', 'old', 'great', 'small', 'large', 'big', 'little',
        'high', 'low', 'long', 'short', 'different', 'same', 'important',
        'public', 'able', 'own', 'other', 'early', 'young', 'few', 'next',
        'last', 'right', 'left', 'sure', 'best', 'better', 'worse', 'worst',

        # Articles, prepositions, conjunctions
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'until',
        'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
        'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to',
        'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',

        # Pronouns
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'them', 'their', 'this',
        'that', 'these', 'those', 'who', 'which', 'what', 'where', 'when', 'why',
        'how', 'all', 'each', 'every', 'both', 'some', 'any', 'many', 'much',

        # Generic actions/UI elements
        'signup', 'sign up', 'login', 'log in', 'logout', 'sign in', 'click here',
        'more', 'less', 'back', 'next', 'previous', 'home', 'menu',
        'subscribe', 'follow', 'share', 'like', 'comment', 'save', 'delete',

        # Vague descriptors
        'men', 'women', 'person', 'man', 'woman', 'child', 'children',
        'sea', 'land', 'water', 'air', 'fire', 'earth', 'sun', 'moon', 'day',
        'night', 'week', 'month', 'year', 'morning', 'evening', 'afternoon',

        # Single letters/numbers (unless they're acronyms)
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
    }

    # Known valid acronyms that shouldn't be removed even if short
    VALID_ACRONYMS = {
        'ai', 'ml', 'ui', 'ux', 'api', 'url', 'css', 'html', 'js', 'sql',
        'aws', 'gcp', 'ios', 'iot', 'vpn', 'cdn', 'dns', 'ssh', 'ssl', 'tls',
        'json', 'xml', 'rest', 'soap', 'http', 'tcp', 'ip', 'ceo', 'cto',
        'cfo', 'hr', 'pr', 'qa', 'ci', 'cd', 'pm', 'dm', 'seo', 'sem',
        'crm', 'erp', 'saas', 'paas', 'iaas', 'llm', 'nlp', 'ocr', 'pdf', 'docker',
        'career', 'people', 'server', 'system', 'user', 'coding', 'search', 'feed',
        'play'
    }

    def __init__(self, api_url: str, token: str, dry_run: bool = True,
                 custom_blocklist: str = None):
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.dry_run = dry_run
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.stats = {
            'tags_analyzed': 0,
            'junk_tags_found': 0,
            'tags_deleted': 0,
            'links_updated': 0,
            'errors': 0
        }

        # Load custom blocklist if provided
        if custom_blocklist:
            self.load_custom_blocklist(custom_blocklist)

    def load_custom_blocklist(self, filename: str):
        """Load additional junk words from a custom file."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        self.JUNK_WORDS.add(line.lower())
            print(f"✓ Loaded custom blocklist from {filename}")
        except FileNotFoundError:
            print(f"⚠ Custom blocklist file not found: {filename}")
        except Exception as e:
            print(f"⚠ Error loading custom blocklist: {e}")

    def fetch_all_tags(self) -> List[Dict]:
        """Fetch all tags from API."""
        try:
            response = requests.get(
                f"{self.api_url}/tags",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            tags = data.get('response', data) if isinstance(data, dict) else data
            return tags
        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching tags: {e}")
            sys.exit(1)

    def is_junk_tag(self, tag_name: str) -> tuple[bool, str]:
        """
        Determine if a tag is junk/non-substantive.
        Returns (is_junk, reason).
        """
        lower_name = tag_name.lower().strip()

        # Check blocklist
        if lower_name in self.JUNK_WORDS:
            return True, "blocklist"

        # Preserve known acronyms
        if lower_name in self.VALID_ACRONYMS:
            return False, "valid_acronym"

        # Too short (unless uppercase acronym)
        if len(lower_name) <= 2:
            if not tag_name.isupper():
                return True, "too_short"

        # Single character
        if len(tag_name) == 1:
            return True, "single_char"

        # All digits
        if tag_name.isdigit():
            return True, "all_digits"

        # Contains only non-alphanumeric
        if not any(c.isalnum() for c in tag_name):
            return True, "no_alphanumeric"

        # Check for common suffixes that indicate generic words
        generic_suffixes = ['ing', 'ed', 'er', 'est', 'ly']
        if any(lower_name.endswith(suffix) and len(lower_name) <= 6 for suffix in generic_suffixes):
            # Short words with common suffixes are often generic
            return True, "generic_suffix"

        return False, ""

    def analyze_tags(self) -> Dict:
        """Analyze all tags and identify junk tags."""
        print("Analyzing tags for junk/non-substantive entries...")

        tags = self.fetch_all_tags()
        self.stats['tags_analyzed'] = len(tags)

        junk_tags = []
        good_tags = []

        for tag in tags:
            tag_name = tag.get('name', '')
            is_junk, reason = self.is_junk_tag(tag_name)

            if is_junk:
                junk_tags.append({
                    'tag': tag,
                    'reason': reason,
                    'usage': tag.get('_count', {}).get('links', 0)
                })
            else:
                good_tags.append(tag)

        self.stats['junk_tags_found'] = len(junk_tags)

        return {
            'junk_tags': junk_tags,
            'good_tags': good_tags,
            'total': len(tags)
        }

    def delete_tag(self, tag_id: str, tag_name: str) -> bool:
        """Delete a tag."""
        if self.dry_run:
            return True

        try:
            response = requests.delete(
                f"{self.api_url}/tags/{tag_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            self.stats['tags_deleted'] += 1
            return True
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error deleting tag '{tag_name}': {e}")
            self.stats['errors'] += 1
            return False

    def remove_junk_tags(self, analysis: Dict, min_usage: int = 0):
        """Remove identified junk tags."""
        junk_tags = analysis['junk_tags']

        if not junk_tags:
            print("✓ No junk tags found!")
            return

        print(f"\n{'='*80}")
        print(f"{'DRY RUN - ' if self.dry_run else ''}REMOVING JUNK TAGS")
        print(f"{'='*80}\n")

        # Sort by usage (delete least-used first)
        junk_tags_sorted = sorted(junk_tags, key=lambda x: x['usage'])

        for item in junk_tags_sorted:
            tag = item['tag']
            tag_id = tag['id']
            tag_name = tag['name']
            usage = item['usage']
            reason = item['reason']

            # Skip if usage is above threshold
            if usage > min_usage and min_usage > 0:
                continue

            print(f"{'[DRY RUN] ' if self.dry_run else ''}Deleting: '{tag_name}' "
                  f"({usage} links, reason: {reason})")

            self.delete_tag(tag_id, tag_name)

            # Rate limiting
            if not self.dry_run:
                time.sleep(0.1)

        self.print_summary()

    def print_analysis_report(self, analysis: Dict):
        """Print detailed analysis report."""
        print(f"\n{'='*80}")
        print("JUNK TAG ANALYSIS REPORT")
        print(f"{'='*80}\n")

        print(f"Total tags analyzed:     {analysis['total']}")
        print(f"Junk tags identified:    {len(analysis['junk_tags'])} "
              f"({len(analysis['junk_tags'])/analysis['total']*100:.1f}%)")
        print(f"Good tags:               {len(analysis['good_tags'])} "
              f"({len(analysis['good_tags'])/analysis['total']*100:.1f}%)")

        # Group by reason
        reasons = {}
        for item in analysis['junk_tags']:
            reason = item['reason']
            reasons[reason] = reasons.get(reason, 0) + 1

        print(f"\n📊 Breakdown by reason:")
        for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
            print(f"  {reason:20s}: {count:4d} tags")

        # Show examples
        print(f"\n📝 Sample junk tags (showing first 50):")
        for i, item in enumerate(analysis['junk_tags'][:50]):
            tag_name = item['tag']['name']
            usage = item['usage']
            reason = item['reason']
            print(f"  '{tag_name}' ({usage} links, {reason})")

        if len(analysis['junk_tags']) > 50:
            print(f"  ... and {len(analysis['junk_tags']) - 50} more")

        # Total link references
        total_link_refs = sum(item['usage'] for item in analysis['junk_tags'])
        print(f"\n⚠️  Total link references to junk tags: {total_link_refs:,}")
        print(f"    (these links will lose these tags when deleted)")

        print(f"\n{'='*80}\n")

    def print_summary(self):
        """Print removal summary."""
        print(f"\n{'='*80}")
        print("REMOVAL SUMMARY")
        print(f"{'='*80}")
        print(f"  Tags deleted:  {self.stats['tags_deleted']:,}")
        print(f"  Errors:        {self.stats['errors']:,}")
        print(f"{'='*80}\n")

        if self.dry_run:
            print("💡 This was a dry run. No changes were made.")
            print("   Run without --dry-run to actually delete junk tags.\n")

    def export_junk_list(self, analysis: Dict, filename: str = "junk_tags.json"):
        """Export junk tags list to file."""
        export_data = {
            'total_tags': analysis['total'],
            'junk_count': len(analysis['junk_tags']),
            'junk_tags': [
                {
                    'name': item['tag']['name'],
                    'id': item['tag']['id'],
                    'usage': item['usage'],
                    'reason': item['reason']
                }
                for item in analysis['junk_tags']
            ]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Exported junk tags list to {filename}")


def main():
    parser = argparse.ArgumentParser(
        description='Remove non-substantive/junk tags from Linkwarden'
    )
    parser.add_argument('--api-url', required=True, help='Linkwarden API URL')
    parser.add_argument('--token', required=True, help='API authentication token')
    parser.add_argument('--analyze', action='store_true',
                       help='Only analyze and report, don\'t remove')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview removal without actually deleting')
    parser.add_argument('--min-usage', type=int, default=0,
                       help='Only delete junk tags with usage <= this value (0 = all)')
    parser.add_argument('--export', type=str,
                       help='Export junk tags list to file')
    parser.add_argument('--blocklist', type=str, default='junk_tags_blocklist.txt',
                       help='Custom blocklist file (default: junk_tags_blocklist.txt)')

    args = parser.parse_args()

    # If analyzing, force dry-run
    if args.analyze:
        args.dry_run = True

    remover = JunkTagRemover(
        args.api_url,
        args.token,
        dry_run=args.dry_run,
        custom_blocklist=args.blocklist
    )

    # Analyze tags
    analysis = remover.analyze_tags()

    # Print report
    remover.print_analysis_report(analysis)

    # Export if requested
    if args.export:
        remover.export_junk_list(analysis, args.export)

    # Remove if not analyze-only
    if not args.analyze:
        print("\n" + "="*80)
        if args.min_usage > 0:
            print(f"Will only delete junk tags with ≤{args.min_usage} uses")

        confirm = input("Proceed with removal? [y/N] ").strip().lower()
        if confirm == 'y':
            remover.remove_junk_tags(analysis, min_usage=args.min_usage)
        else:
            print("Cancelled.")
    else:
        print("💡 Analysis complete. Use without --analyze to remove junk tags.")


if __name__ == '__main__':
    main()
