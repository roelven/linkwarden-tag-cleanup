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

# Get tags
resp = requests.get(f"{API}/tags", headers=headers, timeout=30)
tags_data = resp.json()
tags = tags_data.get('response', tags_data) if isinstance(tags_data, dict) else tags_data

product_tag = [t for t in tags if t['name'] == 'Product'][0]
print("Tag from /tags endpoint:")
print(json.dumps(product_tag, indent=2))

# Get a link and see its tag structure
resp = requests.get(f"{API}/links", headers=headers, timeout=30)
links_data = resp.json()
links = links_data.get('response', links_data) if isinstance(links_data, dict) else links_data

link_with_tags = [l for l in links if l.get('tags')][0]
print("\n\nTag from link.tags:")
print(json.dumps(link_with_tags['tags'][0], indent=2))
