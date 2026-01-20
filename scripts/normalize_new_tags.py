#!/usr/bin/env python3
"""
Linkwarden Tag Normalization Service

Periodic service to normalize tags on newly created/updated links.
Prevents tag proliferation by:
1. Normalizing case (Title Case for words, UPPERCASE for acronyms)
2. Fuzzy matching against existing tags
3. Replacing similar tags with canonical versions

This runs after the LLM has generated tags, providing a post-processing layer.

Usage:
    # Process links modified in last 15 minutes
    python3 normalize_new_tags.py --api-url https://linkwarden.w22.io/api/v1 \
                                   --token YOUR_TOKEN \
                                   --lookback 15

    # Dry run mode
    python3 normalize_new_tags.py --api-url https://linkwarden.w22.io/api/v1 \
                                   --token YOUR_TOKEN \
                                   --lookback 15 \
                                   --dry-run

    # Cron setup (every 5 minutes):
    */5 * * * * /usr/bin/python3 /path/to/normalize_new_tags.py --api-url URL --token TOKEN --lookback 10 >> /var/log/linkwarden-normalize.log 2>&1
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from difflib import SequenceMatcher
import requests


class TagNormalizer:
    # Known acronyms that should be UPPERCASE
    ACRONYMS = {
        'ai', 'api', 'url', 'http', 'https', 'html', 'css', 'js',
        'llm', 'ml', 'ui', 'ux', 'ceo', 'cto', 'cfo', 'cio',
        'nft', 'vr', 'ar', 'iot', 'saas', 'paas', 'iaas',
        'aws', 'gcp', 'gke', 'eks', 'aks',
        'sql', 'nosql', 'json', 'xml', 'yaml', 'csv',
        'rest', 'soap', 'grpc', 'graphql',
        'tcp', 'ip', 'dns', 'ssl', 'tls', 'ssh', 'vpn',
        'cdn', 'ddos', 'xss', 'csrf', 'jwt',
        'ci', 'cd', 'cicd', 'devops', 'mlops',
        'rss', 'seo', 'sem', 'crm', 'erp',
        'pdf', 'docx', 'xlsx', 'pptx', 'svg', 'png', 'jpg', 'gif',
        'ide', 'sdk', 'cli', 'gui', 'tui',
        'os', 'ios', 'macos', 'linux', 'unix',
        'ram', 'cpu', 'gpu', 'ssd', 'hdd',
        'faq', 'qa', 'qc', 'sla', 'kpi', 'roi', 'mvp',
    }

    def __init__(self, api_url: str, token: str, dry_run: bool = False):
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.dry_run = dry_run
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.existing_tags_cache = None
        self.stats = {
            'links_processed': 0,
            'links_updated': 0,
            'tags_normalized': 0,
            'tags_fuzzy_matched': 0,
            'errors': 0
        }

    def fetch_all_existing_tags(self) -> List[Dict]:
        """Fetch and cache all existing tags."""
        if self.existing_tags_cache is not None:
            return self.existing_tags_cache

        try:
            response = requests.get(
                f"{self.api_url}/tags",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            # Handle both direct array and paginated responses
            tags = data.get('response', data) if isinstance(data, dict) else data

            self.existing_tags_cache = tags
            return tags

        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching existing tags: {e}")
            return []

    def fetch_recent_links(self, lookback_minutes: int = 15) -> List[Dict]:
        """Fetch links created/updated in the last N minutes."""
        try:
            # Calculate cutoff time
            cutoff = datetime.utcnow() - timedelta(minutes=lookback_minutes)

            # Fetch recent links
            # Note: Linkwarden API might not support time-based filtering directly
            # We'll fetch all and filter client-side for now
            response = requests.get(
                f"{self.api_url}/links",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            # Handle both direct array and paginated responses
            links = data.get('response', data) if isinstance(data, dict) else data

            # Filter by updatedAt time
            recent_links = []
            for link in links:
                updated_at = link.get('updatedAt')
                if updated_at:
                    # Parse ISO timestamp
                    try:
                        link_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        if link_time >= cutoff:
                            recent_links.append(link)
                    except Exception:
                        continue

            return recent_links

        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching recent links: {e}")
            return []

    def normalize_case(self, tag: str) -> str:
        """Normalize tag case (UPPERCASE for acronyms, Title Case otherwise)."""
        tag_lower = tag.lower()

        # Check if it's a known acronym
        if tag_lower in self.ACRONYMS:
            return tag_lower.upper()

        # Otherwise use Title Case
        return tag.title()

    def find_similar_tag(self, tag: str, existing_tags: List[Dict],
                        threshold: float = 0.85) -> Optional[str]:
        """Find similar tag using fuzzy matching."""
        tag_lower = tag.lower()

        for existing in existing_tags:
            existing_name = existing.get('name', '')
            existing_lower = existing_name.lower()

            # Exact match (case-insensitive)
            if tag_lower == existing_lower:
                return existing_name

            # Fuzzy match
            similarity = SequenceMatcher(None, tag_lower, existing_lower).ratio()
            if similarity >= threshold:
                return existing_name

        return None

    def normalize_tag(self, tag: str, existing_tags: List[Dict],
                     similarity_threshold: float = 0.85) -> str:
        """Normalize a single tag."""
        # First, try fuzzy matching against existing tags
        similar = self.find_similar_tag(tag, existing_tags, similarity_threshold)
        if similar:
            self.stats['tags_fuzzy_matched'] += 1
            return similar

        # No match found, just normalize case
        normalized = self.normalize_case(tag)
        if normalized != tag:
            self.stats['tags_normalized'] += 1

        return normalized

    def normalize_link_tags(self, link: Dict, existing_tags: List[Dict],
                           similarity_threshold: float = 0.85) -> Optional[List[str]]:
        """
        Normalize all tags for a link.
        Returns new tag list if changes were made, None otherwise.
        """
        current_tags = link.get('tags', [])
        if not current_tags:
            return None

        # Extract tag names
        tag_names = [t.get('name', '') for t in current_tags if t.get('name')]
        if not tag_names:
            return None

        # Normalize each tag
        normalized_tags = []
        changed = False

        for tag in tag_names:
            normalized = self.normalize_tag(tag, existing_tags, similarity_threshold)

            if normalized != tag:
                changed = True

            # Avoid duplicates in normalized list
            if normalized not in normalized_tags:
                normalized_tags.append(normalized)

        return normalized_tags if changed else None

    def fetch_link_by_id(self, link_id: str) -> Optional[Dict]:
        """Fetch a single link by ID."""
        try:
            response = requests.get(
                f"{self.api_url}/links/{link_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            # Handle wrapped response
            if isinstance(data, dict) and 'response' in data:
                return data['response']
            return data
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error fetching link {link_id}: {e}")
            return None

    def update_link_tags(self, link_id: str, new_tag_names: List[str],
                        existing_tags: List[Dict]) -> bool:
        """Update tags for a link."""
        if self.dry_run:
            return True

        try:
            # IMPORTANT: Linkwarden API requires the FULL link object
            # We can't just send {"tags": [...]}
            # We must GET the full link, modify tags, then PUT it back

            link = self.fetch_link_by_id(link_id)
            if not link:
                return False

            # Build lookup map: tag name -> full tag object (without _count)
            tag_map = {}
            for tag in existing_tags:
                clean_tag = {k: v for k, v in tag.items() if k != '_count'}
                tag_map[tag['name']] = clean_tag

            # Convert tag names to full tag objects (with IDs)
            new_tags = []
            for name in new_tag_names:
                if name in tag_map:
                    # Existing tag - use full object with ID
                    new_tags.append(tag_map[name])
                else:
                    # New tag - API will create it
                    new_tags.append({'name': name})

            link['tags'] = new_tags

            # Send the complete link object back
            response = requests.put(
                f"{self.api_url}/links/{link_id}",
                headers=self.headers,
                json=link,
                timeout=30
            )
            response.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            error_detail = ""
            try:
                if hasattr(e.response, 'text'):
                    error_detail = f" - {e.response.text[:200]}"
            except:
                pass
            print(f"  ✗ Error updating link {link_id}: {e}{error_detail}")
            return False

    def process_recent_links(self, lookback_minutes: int = 15,
                            similarity_threshold: float = 0.85):
        """Process and normalize tags on recent links."""
        print(f"\n{'='*80}")
        print(f"TAG NORMALIZATION SERVICE {'(DRY RUN)' if self.dry_run else ''}")
        print(f"{'='*80}")
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print(f"Lookback: {lookback_minutes} minutes")
        print(f"Similarity threshold: {similarity_threshold}")

        # Fetch existing tags for fuzzy matching
        print(f"\n📋 Fetching existing tags...")
        existing_tags = self.fetch_all_existing_tags()
        print(f"  ✓ Found {len(existing_tags)} existing tags")

        # Fetch recent links
        print(f"\n🔍 Fetching recent links...")
        recent_links = self.fetch_recent_links(lookback_minutes)
        print(f"  ✓ Found {len(recent_links)} links modified in last {lookback_minutes} minutes")

        if not recent_links:
            print(f"\n✓ No recent links to process")
            return

        # Process each link
        print(f"\n🏷️  Processing links...")
        for link in recent_links:
            self.stats['links_processed'] += 1
            link_id = link['id']
            link_url = link.get('url', 'unknown')

            # Normalize tags
            normalized_tags = self.normalize_link_tags(link, existing_tags, similarity_threshold)

            if normalized_tags:
                old_tags = [t.get('name') for t in link.get('tags', [])]
                print(f"\n  Link: {link_url}")
                print(f"    Old tags: {old_tags}")
                print(f"    New tags: {normalized_tags}")

                if self.update_link_tags(link_id, normalized_tags, existing_tags):
                    self.stats['links_updated'] += 1
                    print(f"    ✓ {'Would update' if self.dry_run else 'Updated'}")
                else:
                    self.stats['errors'] += 1

                # Rate limiting
                time.sleep(0.1)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print processing summary."""
        print(f"\n{'='*80}")
        print("NORMALIZATION SUMMARY")
        print(f"{'='*80}")
        print(f"  Links processed:      {self.stats['links_processed']:,}")
        print(f"  Links updated:        {self.stats['links_updated']:,}")
        print(f"  Tags normalized:      {self.stats['tags_normalized']:,}")
        print(f"  Tags fuzzy matched:   {self.stats['tags_fuzzy_matched']:,}")
        print(f"  Errors:               {self.stats['errors']:,}")
        print(f"{'='*80}")

        if self.dry_run:
            print("\n💡 This was a dry run. No changes were made.")
        else:
            print(f"\n✓ Normalization complete at {datetime.utcnow().isoformat()}")


def main():
    parser = argparse.ArgumentParser(description='Normalize Linkwarden tags on recent links')
    parser.add_argument('--api-url', required=True, help='Linkwarden API URL')
    parser.add_argument('--token', required=True, help='API authentication token')
    parser.add_argument('--lookback', type=int, default=15,
                       help='Process links modified in last N minutes (default: 15)')
    parser.add_argument('--similarity-threshold', type=float, default=0.85,
                       help='Fuzzy matching threshold 0-1 (default: 0.85)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without applying them')

    args = parser.parse_args()

    # Validate threshold
    if not 0 <= args.similarity_threshold <= 1:
        print("✗ Similarity threshold must be between 0 and 1")
        sys.exit(1)

    # Create normalizer and process
    normalizer = TagNormalizer(args.api_url, args.token, dry_run=args.dry_run)
    normalizer.process_recent_links(args.lookback, args.similarity_threshold)


if __name__ == '__main__':
    main()
