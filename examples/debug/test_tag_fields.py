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

# Get product tag
resp = requests.get(f"{API}/tags", headers=headers, timeout=30)
tags = resp.json().get('response', resp.json())
product_tag = [t for t in tags if t['name'] == 'Product'][0]

# Get a link with product tag
resp = requests.get(f"{API}/links", headers=headers, params={'tagId': 3}, timeout=30)
links = resp.json().get('response', resp.json())
if not links:
    print("No links found")
    sys.exit(0)

test_link = links[0]
link_id = test_link['id']

# Get full link
resp = requests.get(f"{API}/links/{link_id}", headers=headers, timeout=30)
full_link = resp.json()

print(f"Testing link {link_id}")
print(f"Current tags: {[t['name'] for t in full_link.get('tags', [])]}")

# Test 1: Use tag WITH _count
print("\n=== Test 1: Tag with _count field ===")
test_tag = product_tag.copy()
full_link['tags'] = [test_tag]
resp = requests.put(f"{API}/links/{link_id}", headers=headers, json=full_link, timeout=30)
print(f"Status: {resp.status_code}")
if resp.status_code != 200:
    print(f"Error: {resp.text[:200]}")

# Test 2: Remove _count
print("\n=== Test 2: Tag WITHOUT _count field ===")
test_tag = product_tag.copy()
test_tag.pop('_count', None)
full_link['tags'] = [test_tag]
resp = requests.put(f"{API}/links/{link_id}", headers=headers, json=full_link, timeout=30)
print(f"Status: {resp.status_code}")
if resp.status_code != 200:
    print(f"Error: {resp.text[:200]}")
else:
    print("✓ SUCCESS!")
