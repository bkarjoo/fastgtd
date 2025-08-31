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

# Create a note with obvious title
print("\n=== Create DEBUG note ===")
note_data = {
    "node_type": "note",
    "title": "🔴 DEBUG NOTE - CHECK TAGS HERE",
    "parent_id": None,
    "sort_order": 999,
    "note_data": {
        "body": "# Debug Note\n\nThis note should have tags visible above this content.\n\nYou should see:\n1. A RED BORDER around this content\n2. A YELLOW section above with tags\n3. Console logs with 🔴 DEBUG messages"
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

# Create or get a tag
print("\n=== Create/Get tags ===")
response = requests.get("http://localhost:8003/tags/", headers=headers)
if response.status_code == 200:
    existing_tags = response.json()
    if existing_tags:
        tag1_id = existing_tags[0]['id']
        tag1_name = existing_tags[0]['name']
        print(f"✓ Using existing tag: {tag1_name}")
    else:
        # Create a tag if none exist
        tag_list_response = requests.get("http://localhost:8003/tag-lists/", headers=headers)
        if tag_list_response.status_code == 200:
            tag_lists = tag_list_response.json()
            if tag_lists:
                tag_list_id = tag_lists[0]['id']
                tag_data = {
                    "name": "DEBUG-TAG",
                    "tag_list_id": tag_list_id,
                    "color": "#FF0000"
                }
                tag_response = requests.post("http://localhost:8003/tags/", json=tag_data, headers=headers)
                if tag_response.status_code == 200:
                    tag = tag_response.json()
                    tag1_id = tag['id']
                    tag1_name = tag['name']
                    print(f"✓ Created tag: {tag1_name}")

# Add multiple tags to the note
print("\n=== Add tags to note ===")
response = requests.post(f"http://localhost:8003/nodes/{note_id}/tags/{tag1_id}", headers=headers)
if response.status_code in [200, 201]:
    print(f"✓ Added tag '{tag1_name}' to note")
else:
    print(f"✗ Failed to add tag: {response.status_code}")

# Get note with tags
print("\n=== Verify note has tags ===")
response = requests.get(f"http://localhost:8003/nodes/{note_id}", headers=headers)
if response.status_code == 200:
    note = response.json()
    print(f"✓ Retrieved note: {note['title']}")
    if 'tags' in note and note['tags']:
        print(f"✓ Note has {len(note['tags'])} tag(s): {', '.join([tag['name'] for tag in note['tags']])}")
    else:
        print(f"✗ WARNING: Note has NO tags in response!")

print("\n" + "="*50)
print("🔴 DEBUG INSTRUCTIONS:")
print("="*50)
print("1. Open the note '🔴 DEBUG NOTE - CHECK TAGS HERE' in the UI")
print("2. You should see:")
print("   - RED BORDER around the note content")
print("   - YELLOW SECTION above content with tags")
print("3. Open browser console (F12)")
print("4. Look for 🔴 DEBUG messages")
print("5. Report what you see!")
print("="*50)