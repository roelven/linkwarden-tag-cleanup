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

print("FINAL TEST - Merge product → Product")

# Get tags
resp = requests.get(f"{API}/tags", headers=headers, timeout=30)
tags = resp.json().get('response', resp.json())
product_tag = [t for t in tags if t['name'] == 'Product'][0]

# Get link with 'product'
resp = requests.get(f"{API}/links", headers=headers, params={'tagId': 3}, timeout=30)
links = resp.json().get('response', resp.json())
if not links:
    print("✓ No links with 'product' tag")
    sys.exit(0)

link_id = links[0]['id']
print(f"Testing with link {link_id}")

# Fetch full link - EXTRACT FROM RESPONSE WRAPPER
resp = requests.get(f"{API}/links/{link_id}", headers=headers, timeout=30)
data = resp.json()
full_link = data.get('response', data) if isinstance(data, dict) and 'response' in data else data

print(f"Current tags: {[t['name'] for t in full_link.get('tags', [])]}")

# Clean and merge
current_tags = full_link.get('tags', [])
new_tags = [t for t in current_tags if t['name'] != 'product']
has_product = any(t['name'] == 'Product' for t in new_tags)
if not has_product:
    # Clean tag - remove _count
    clean_tag = {k: v for k, v in product_tag.items() if k != '_count'}
    new_tags.append(clean_tag)

full_link['tags'] = new_tags
print(f"New tags: {[t['name'] for t in new_tags]}")

# Update
resp = requests.put(f"{API}/links/{link_id}", headers=headers, json=full_link, timeout=30)
print(f"\nStatus: {resp.status_code}")
if resp.status_code == 200:
    print("✅ SUCCESS! Tag merge works!")
else:
    print(f"✗ Error: {resp.text[:300]}")
    sys.exit(1)
