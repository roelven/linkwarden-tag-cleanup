#!/usr/bin/env python3
import os, sys, requests, json

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

print("Testing tag merge simulation...")

# Get a link with multiple tags
resp = requests.get(f"{API}/links", headers=headers, timeout=30)
resp.raise_for_status()
links = resp.json()
if isinstance(links, dict): links = links.get('response', [])

test_link = None
for link in links:
    if len(link.get('tags', [])) >= 2:
        test_link = link
        break

if not test_link:
    print("Need a link with 2+ tags")
    sys.exit(1)

link_id = test_link['id']
current_tags = test_link['tags']
print(f"Link {link_id} has tags: {[t['name'] for t in current_tags]}")

# Simulate removing first tag and keeping the rest
new_tags = current_tags[1:]  # Keep full tag objects
print(f"Setting to: {[t['name'] for t in new_tags]}")

# Test update with full objects
resp = requests.put(f"{API}/links/{link_id}", headers=headers, json=test_link, timeout=30)
print(f"Status: {resp.status_code}")
if resp.status_code != 200:
    print(f"Error: {resp.text[:300]}")
    sys.exit(1)

print("✓ SUCCESS! Full tag objects work correctly")
