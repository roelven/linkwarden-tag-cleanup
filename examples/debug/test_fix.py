#!/usr/bin/env python3
"""Quick test to verify the API fix works."""

import os
import sys
import requests

# Load .env
try:
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
except:
    pass

API_URL = os.environ.get('LINKWARDEN_API_URL', '').rstrip('/')
TOKEN = os.environ.get('LINKWARDEN_TOKEN', '')

if not API_URL or not TOKEN:
    print("Error: Configure .env file")
    sys.exit(1)

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

print("Testing fixed API call...")

# Get a link
response = requests.get(f"{API_URL}/links", headers=headers, timeout=30)
response.raise_for_status()
links = response.json()
if isinstance(links, dict):
    links = links.get('response', [])

if not links:
    print("No links found")
    sys.exit(1)

test_link = links[0]
link_id = test_link['id']
print(f"Testing with link ID: {link_id}")
print(f"Current tags: {[t['name'] for t in test_link.get('tags', [])]}")

# Try to update it (with same tags - no actual change)
test_link['tags'] = test_link.get('tags', [])

response = requests.put(
    f"{API_URL}/links/{link_id}",
    headers=headers,
    json=test_link,
    timeout=30
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✓ SUCCESS! API call works correctly")
else:
    print(f"✗ FAILED: {response.text[:200]}")
    sys.exit(1)
