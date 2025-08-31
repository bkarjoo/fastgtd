#!/usr/bin/env python3
"""
Simple test to verify basic smart folder functionality
"""
import requests
import json

# Login first
login_response = requests.post("http://localhost:8003/auth/login", json={
    "email": "test@example.com",
    "password": "test123"
})

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ Logged in")

# Test 1: Create a simple smart folder
print("\n=== Test 1: Create Smart Folder ===")
smart_folder_data = {
    "node_type": "smart_folder",
    "title": "Test Smart Folder",
    "parent_id": None,
    "sort_order": 1
}

response = requests.post("http://localhost:8003/nodes/", json=smart_folder_data, headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    smart_folder = response.json()
    print(f"✓ Created smart folder with ID: {smart_folder['id']}")
    smart_folder_id = smart_folder['id']
else:
    print(f"❌ Failed to create smart folder")
    print(response.text)
    exit(1)

# Test 2: Get smart folder contents (should be empty)
print("\n=== Test 2: Get Smart Folder Contents ===")
response = requests.get(f"http://localhost:8003/nodes/{smart_folder_id}/contents", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    contents = response.json()
    print(f"✓ Got contents: {len(contents)} items")
else:
    print(f"❌ Failed to get contents")
    print(response.text)

print("\n✅ Basic test complete")