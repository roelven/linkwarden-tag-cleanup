#!/usr/bin/env python3
"""
Quick debug script to test Linkwarden API and find correct payload format.
"""

import os
import sys
import json
import requests

# Load from .env if available
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
    print("Error: Set LINKWARDEN_API_URL and LINKWARDEN_TOKEN in .env")
    sys.exit(1)

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

print("Testing Linkwarden API...")
print(f"API URL: {API_URL}")
print()

# Step 1: Fetch a single link to see its structure
print("1. Fetching a sample link...")
response = requests.get(f"{API_URL}/links", headers=headers, timeout=30)
response.raise_for_status()
links = response.json()

if isinstance(links, dict):
    links = links.get('response', [])

if not links:
    print("No links found!")
    sys.exit(1)

sample_link = links[0]
link_id = sample_link['id']

print(f"   Link ID: {link_id}")
print(f"   URL: {sample_link.get('url', 'N/A')}")
print(f"   Current tags: {json.dumps(sample_link.get('tags', []), indent=2)}")
print()

# Step 2: Try different payload formats to update tags
current_tags = sample_link.get('tags', [])

if not current_tags:
    print("This link has no tags. Please manually add a tag first for testing.")
    sys.exit(1)

print("2. Testing different payload formats...")
print()

# Format 1: Array of objects with 'name'
print("Format 1: tags as array of {name: 'TagName'}")
payload1 = {
    'tags': [{'name': tag['name']} for tag in current_tags]
}
print(f"   Payload: {json.dumps(payload1, indent=2)}")
try:
    resp = requests.put(
        f"{API_URL}/links/{link_id}",
        headers=headers,
        json=payload1,
        timeout=30
    )
    print(f"   Status: {resp.status_code}")
    if resp.status_code >= 400:
        print(f"   Error: {resp.text[:300]}")
    else:
        print(f"   Success!")
except Exception as e:
    print(f"   Exception: {e}")
print()

# Format 2: Array of objects with 'id'
print("Format 2: tags as array of {id: tagId}")
payload2 = {
    'tags': [{'id': tag['id']} for tag in current_tags if 'id' in tag]
}
print(f"   Payload: {json.dumps(payload2, indent=2)}")
try:
    resp = requests.put(
        f"{API_URL}/links/{link_id}",
        headers=headers,
        json=payload2,
        timeout=30
    )
    print(f"   Status: {resp.status_code}")
    if resp.status_code >= 400:
        print(f"   Error: {resp.text[:300]}")
    else:
        print(f"   Success!")
except Exception as e:
    print(f"   Exception: {e}")
print()

# Format 3: Array of tag IDs
print("Format 3: tags as array of IDs")
payload3 = {
    'tags': [tag['id'] for tag in current_tags if 'id' in tag]
}
print(f"   Payload: {json.dumps(payload3, indent=2)}")
try:
    resp = requests.put(
        f"{API_URL}/links/{link_id}",
        headers=headers,
        json=payload3,
        timeout=30
    )
    print(f"   Status: {resp.status_code}")
    if resp.status_code >= 400:
        print(f"   Error: {resp.text[:300]}")
    else:
        print(f"   Success!")
except Exception as e:
    print(f"   Exception: {e}")
print()

# Format 4: Full link object
print("Format 4: Full link object with tags")
payload4 = sample_link.copy()
payload4['tags'] = current_tags
print(f"   Payload keys: {list(payload4.keys())}")
try:
    resp = requests.put(
        f"{API_URL}/links/{link_id}",
        headers=headers,
        json=payload4,
        timeout=30
    )
    print(f"   Status: {resp.status_code}")
    if resp.status_code >= 400:
        print(f"   Error: {resp.text[:300]}")
    else:
        print(f"   Success!")
except Exception as e:
    print(f"   Exception: {e}")
print()

print("Done! Check which format succeeded above.")
