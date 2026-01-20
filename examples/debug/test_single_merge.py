#!/usr/bin/env python3
"""Test merging a single tag to verify the fix."""

import os
import sys
import requests
import time

# Load .env
try:
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v
except: pass

API = os.environ.get('LINKWARDEN_API_URL', '').rstrip('/')
TOKEN = os.environ.get('LINKWARDEN_TOKEN', '')
headers = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}

print("Testing single tag merge with correct API format...")

# Find the 'product' and 'Product' tags
resp = requests.get(f"{API}/tags", headers=headers, timeout=30)
resp.raise_for_status()
tags_data = resp.json()
tags = tags_data.get('response', tags_data) if isinstance(tags_data, dict) else tags_data

product_lower = None
product_upper = None

for tag in tags:
    if tag['name'] == 'product':
        product_lower = tag
    elif tag['name'] == 'Product':
        product_upper = tag

if not product_lower:
    print("✓ Tag 'product' already merged or doesn't exist")
    sys.exit(0)

if not product_upper:
    print("✗ Target tag 'Product' not found!")
    sys.exit(1)

print(f"Found: 'product' (ID {product_lower['id']})")
print(f"Found: 'Product' (ID {product_upper['id']})")

# Get first link with 'product' tag
resp = requests.get(f"{API}/links", headers=headers, params={'tagId': product_lower['id']}, timeout=30)
resp.raise_for_status()
links_data = resp.json()
links = links_data.get('response', links_data) if isinstance(links_data, dict) else links_data

if not links:
    print("✓ No links with 'product' tag")
    sys.exit(0)

test_link = links[0]
link_id = test_link['id']
print(f"\nTesting with link {link_id}")
print(f"Current tags: {[t['name'] for t in test_link.get('tags', [])]}")

# Fetch full link object
resp = requests.get(f"{API}/links/{link_id}", headers=headers, timeout=30)
resp.raise_for_status()
full_link = resp.json()

# Remove 'product' tag, add 'Product' tag (full object with ID)
current_tags = full_link.get('tags', [])
new_tags = [t for t in current_tags if t['name'] != 'product']

# Check if 'Product' already on link
has_product_upper = any(t['name'] == 'Product' for t in new_tags)
if not has_product_upper:
    # Add the FULL Product tag object (with ID)
    new_tags.append(product_upper)

print(f"New tags: {[t['name'] for t in new_tags]}")

# Update link
full_link['tags'] = new_tags
resp = requests.put(f"{API}/links/{link_id}", headers=headers, json=full_link, timeout=30)
print(f"\nAPI Response: {resp.status_code}")

if resp.status_code == 200:
    print("✓ SUCCESS! Tag merge works correctly")
    print("\nVerifying change...")
    time.sleep(0.5)
    resp = requests.get(f"{API}/links/{link_id}", headers=headers, timeout=30)
    verify_link = resp.json()
    print(f"Verified tags: {[t['name'] for t in verify_link.get('tags', [])]}")
else:
    print(f"✗ FAILED: {resp.text[:300]}")
    sys.exit(1)
