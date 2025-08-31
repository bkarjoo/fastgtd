#!/usr/bin/env python3
import requests
import json

# Login to get token
login_data = {
    "email": "test@example.com",
    "password": "test123"
}

login_response = requests.post("http://localhost:8003/auth/login", json=login_data)
if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"✓ Logged in successfully")
else:
    print(f"✗ Login failed: {login_response.status_code}")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Create a note
print("\n=== Create a note ===")
note_data = {
    "node_type": "note",
    "title": "Test Note with Tags",
    "parent_id": None,
    "sort_order": 300,
    "note_data": {
        "body": "# Test Note\n\nThis is a test note to verify tag display works properly."
    }
}

response = requests.post("http://localhost:8003/nodes/", json=note_data, headers=headers)
if response.status_code == 200:
    note = response.json()
    print(f"✓ Created note: {note['title']} (id: {note['id']})")
    note_id = note['id']
else:
    print(f"✗ Failed to create note: {response.status_code}")
    exit(1)

# Get existing tags
response = requests.get("http://localhost:8003/tags/", headers=headers)
if response.status_code == 200:
    existing_tags = response.json()
    if existing_tags:
        # Add first tag to the note
        tag_id = existing_tags[0]['id']
        tag_name = existing_tags[0]['name']
        
        response = requests.post(f"http://localhost:8003/nodes/{note_id}/tags/{tag_id}", headers=headers)
        if response.status_code in [200, 201]:
            print(f"✓ Added tag '{tag_name}' to note")
        else:
            print(f"✗ Failed to add tag: {response.status_code}")

# Get note with tags
print("\n=== Get note with tags ===")
response = requests.get(f"http://localhost:8003/nodes/{note_id}", headers=headers)
if response.status_code == 200:
    note = response.json()
    print(f"✓ Retrieved note: {note['title']}")
    if 'tags' in note and note['tags']:
        print(f"  Tags: {', '.join([tag['name'] for tag in note['tags']])}")
    else:
        print(f"  No tags found")
else:
    print(f"✗ Failed to get note: {response.status_code}")

print("\n✅ Note tag test completed!")
print("\n📱 Now open the note in the UI to test:")
print("1. Click on the note to open note view - tags should display")
print("2. Click tag icon in note view - should open tag modal")
print("3. Click edit button - tags should still display")
print("4. Click tag icon in edit mode - should open tag modal")