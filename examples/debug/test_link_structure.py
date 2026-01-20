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

# Get a link via GET /links/{id}
link_id = 4274
resp = requests.get(f"{API}/links/{link_id}", headers=headers, timeout=30)
full_link = resp.json()

print("Link structure:")
print(json.dumps(full_link, indent=2)[:1000])

# Try to PUT it back unchanged
print("\n\nTesting PUT with unchanged link...")
resp = requests.put(f"{API}/links/{link_id}", headers=headers, json=full_link, timeout=30)
print(f"Status: {resp.status_code}")
if resp.status_code != 200:
    print(f"Error: {resp.text[:500]}")
else:
    print("✓ SUCCESS - unchanged link can be PUT back")
