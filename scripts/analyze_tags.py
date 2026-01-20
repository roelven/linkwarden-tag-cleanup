#!/usr/bin/env python3
"""
Linkwarden Tag Analysis Script

Analyzes tags in Linkwarden instance and generates consolidation mappings.
Identifies:
- Case-sensitive duplicates (e.g., "Music" vs "music")
- Semantic overlaps (e.g., "AI", "ML", "Machine Learning")
- Low-usage tags
- Unused tags

Usage:
    python3 analyze_tags.py --api-url https://linkwarden.w22.io/api/v1 --token YOUR_TOKEN
"""

import argparse
import json
import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple
from difflib import SequenceMatcher
import requests


class TagAnalyzer:
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self.tags = []

    def fetch_tags(self) -> List[Dict]:
        """Fetch all tags from Linkwarden API."""
        print("Fetching tags from API...")
        try:
            response = requests.get(
                f"{self.api_url}/tags",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            # Handle both direct array and paginated responses
            if isinstance(data, dict) and 'response' in data:
                self.tags = data['response']
            elif isinstance(data, list):
                self.tags = data
            else:
                self.tags = []

            print(f"✓ Fetched {len(self.tags)} tags")
            return self.tags

        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching tags: {e}")
            sys.exit(1)

    def save_tags_backup(self, filename: str = "tags_backup.json"):
        """Save raw tag data as backup."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.tags, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved tag backup to {filename}")

    def analyze_usage_statistics(self) -> Dict:
        """Analyze tag usage patterns."""
        if not self.tags:
            return {}

        usage_counts = [tag.get('_count', {}).get('links', 0) for tag in self.tags]

        stats = {
            'total_tags': len(self.tags),
            'unused_tags': sum(1 for c in usage_counts if c == 0),
            'single_use_tags': sum(1 for c in usage_counts if c == 1),
            'low_use_tags': sum(1 for c in usage_counts if c <= 3),
            'high_use_tags': sum(1 for c in usage_counts if c >= 10),
            'total_links': sum(usage_counts),
            'avg_usage': sum(usage_counts) / len(usage_counts) if usage_counts else 0
        }

        return stats

    def find_case_duplicates(self) -> Dict[str, List[Dict]]:
        """Find tags that differ only by case."""
        case_groups = defaultdict(list)

        for tag in self.tags:
            tag_name = tag.get('name', '')
            if not tag_name:
                continue
            key = tag_name.lower()
            case_groups[key].append(tag)

        # Filter to only groups with multiple variants
        duplicates = {k: v for k, v in case_groups.items() if len(v) > 1}

        return duplicates

    def find_semantic_overlaps(self, similarity_threshold: float = 0.8) -> Dict[str, List[str]]:
        """Find semantically similar tags using fuzzy matching."""
        overlaps = defaultdict(set)
        tag_names = [tag['name'] for tag in self.tags if tag.get('name')]

        # Predefined semantic groups based on domain knowledge
        semantic_groups = {
            'AI': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'llm', 'llms', 'deep learning'],
            'Technology': ['technology', 'tech', 'technical'],
            'Product': ['product', 'products'],
            'Business': ['business', 'company', 'enterprise'],
            'Design': ['design', 'designer', 'designers'],
            'Development': ['development', 'developer', 'dev', 'developers'],
            'Data': ['data', 'database', 'databases', 'analytics'],
            'Security': ['security', 'cybersecurity', 'privacy'],
            'Internet': ['network', 'networking', 'internet'],
            'Software': ['software', 'application', 'app', 'applications', 'apps'],
            'API': ['api', 'apis'],
            'Web': ['web', 'website', 'websites'],
            'Mobile': ['mobile', 'ios', 'android'],
        }

        # Check which tags match our predefined groups
        tag_names_lower = {name.lower(): name for name in tag_names}

        for canonical, variants in semantic_groups.items():
            matching_tags = []
            for variant in variants:
                if variant in tag_names_lower:
                    matching_tags.append(tag_names_lower[variant])

            if len(matching_tags) > 1:
                overlaps[canonical] = matching_tags

        return dict(overlaps)

    def generate_consolidation_mapping(self,
                                      low_use_threshold: int = 3,
                                      delete_low_use: bool = True) -> Dict:
        """Generate mapping of old tags to new canonical tags."""
        mapping = {
            'case_normalizations': {},
            'semantic_consolidations': {},
            'tags_to_delete': [],
            'statistics': {}
        }

        # 1. Case normalizations
        case_dupes = self.find_case_duplicates()
        for lower_key, variants in case_dupes.items():
            # Sort by usage count (descending)
            sorted_variants = sorted(
                variants,
                key=lambda x: x.get('_count', {}).get('links', 0),
                reverse=True
            )

            # Choose canonical form
            canonical = self.choose_canonical_form([v['name'] for v in sorted_variants])

            # Map all variants to canonical
            for variant in sorted_variants:
                if variant['name'] != canonical:
                    mapping['case_normalizations'][variant['name']] = canonical

        # 2. Semantic consolidations
        semantic_overlaps = self.find_semantic_overlaps()
        for canonical, variants in semantic_overlaps.items():
            for variant in variants:
                if variant != canonical:
                    mapping['semantic_consolidations'][variant] = canonical

        # 3. Tags to delete (low usage)
        if delete_low_use:
            for tag in self.tags:
                tag_name = tag.get('name', '')
                usage = tag.get('_count', {}).get('links', 0)

                # Skip if already in consolidation mappings
                if (tag_name in mapping['case_normalizations'] or
                    tag_name in mapping['semantic_consolidations']):
                    continue

                if usage < low_use_threshold:
                    mapping['tags_to_delete'].append({
                        'name': tag_name,
                        'id': tag.get('id'),
                        'usage': usage
                    })

        # 4. Statistics
        mapping['statistics'] = {
            'total_case_normalizations': len(mapping['case_normalizations']),
            'total_semantic_consolidations': len(mapping['semantic_consolidations']),
            'total_deletions': len(mapping['tags_to_delete']),
            'estimated_final_tag_count': (
                len(self.tags) -
                len(mapping['case_normalizations']) -
                len(mapping['semantic_consolidations']) -
                len(mapping['tags_to_delete'])
            )
        }

        return mapping

    def choose_canonical_form(self, variants: List[str]) -> str:
        """Choose the canonical form for a group of case variants."""
        # Known acronyms should be uppercase
        acronyms = {'ai', 'api', 'url', 'http', 'https', 'html', 'css', 'js',
                   'llm', 'ml', 'ui', 'ux', 'ceo', 'cto', 'nft', 'vr', 'ar',
                   'iot', 'saas', 'paas', 'aws', 'gcp', 'sql', 'json', 'xml',
                   'rest', 'soap', 'tcp', 'ip', 'dns', 'ssl', 'tls', 'ssh'}

        lower_form = variants[0].lower()

        if lower_form in acronyms:
            return lower_form.upper()

        # Otherwise, use Title Case
        return variants[0].title()

    def print_analysis_report(self, mapping: Dict):
        """Print a human-readable analysis report."""
        print("\n" + "="*80)
        print("LINKWARDEN TAG ANALYSIS REPORT")
        print("="*80)

        stats = self.analyze_usage_statistics()
        print("\n📊 Current Tag Statistics:")
        print(f"  Total tags:        {stats['total_tags']:,}")
        print(f"  Unused tags:       {stats['unused_tags']:,} ({stats['unused_tags']/stats['total_tags']*100:.1f}%)")
        print(f"  Single-use tags:   {stats['single_use_tags']:,} ({stats['single_use_tags']/stats['total_tags']*100:.1f}%)")
        print(f"  Low-use tags (≤3): {stats['low_use_tags']:,} ({stats['low_use_tags']/stats['total_tags']*100:.1f}%)")
        print(f"  High-use tags (≥10): {stats['high_use_tags']:,} ({stats['high_use_tags']/stats['total_tags']*100:.1f}%)")
        print(f"  Average usage:     {stats['avg_usage']:.1f} links per tag")

        print("\n🔄 Proposed Consolidations:")
        print(f"  Case normalizations:     {mapping['statistics']['total_case_normalizations']:,}")
        print(f"  Semantic consolidations: {mapping['statistics']['total_semantic_consolidations']:,}")
        print(f"  Tags to delete:          {mapping['statistics']['total_deletions']:,}")

        print("\n📉 Expected Outcome:")
        print(f"  Final tag count:   {mapping['statistics']['estimated_final_tag_count']:,}")
        print(f"  Reduction:         {stats['total_tags'] - mapping['statistics']['estimated_final_tag_count']:,} tags")
        print(f"  Reduction rate:    {(stats['total_tags'] - mapping['statistics']['estimated_final_tag_count'])/stats['total_tags']*100:.1f}%")

        # Show sample consolidations
        print("\n📝 Sample Case Normalizations (showing first 20):")
        for i, (old, new) in enumerate(list(mapping['case_normalizations'].items())[:20]):
            print(f"  '{old}' → '{new}'")

        if len(mapping['case_normalizations']) > 20:
            print(f"  ... and {len(mapping['case_normalizations']) - 20} more")

        print("\n📝 Semantic Consolidations:")
        for old, new in sorted(mapping['semantic_consolidations'].items()):
            print(f"  '{old}' → '{new}'")

        print("\n" + "="*80)
        print(f"✓ Analysis complete. Mapping saved to consolidation_mapping.json")
        print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Analyze Linkwarden tags')
    parser.add_argument('--api-url', required=True, help='Linkwarden API URL')
    parser.add_argument('--token', required=True, help='API authentication token')
    parser.add_argument('--low-use-threshold', type=int, default=3,
                       help='Threshold for low-usage tags (default: 3)')
    parser.add_argument('--no-delete-low-use', action='store_true',
                       help='Do not mark low-usage tags for deletion')
    parser.add_argument('--output', default='consolidation_mapping.json',
                       help='Output file for consolidation mapping')

    args = parser.parse_args()

    analyzer = TagAnalyzer(args.api_url, args.token)

    # Fetch and backup tags
    analyzer.fetch_tags()
    analyzer.save_tags_backup()

    # Generate consolidation mapping
    mapping = analyzer.generate_consolidation_mapping(
        low_use_threshold=args.low_use_threshold,
        delete_low_use=not args.no_delete_low_use
    )

    # Save mapping
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    # Print report
    analyzer.print_analysis_report(mapping)


if __name__ == '__main__':
    main()
