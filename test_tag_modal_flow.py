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

# Create a test note
print("\n=== Create test note ===")
note_data = {
    "node_type": "note",
    "title": "🔴 TEST TAG MODAL - Click me and press tag icon",
    "parent_id": None,
    "sort_order": 1000,
    "note_data": {
        "body": "# Tag Modal Test\n\nUse this note to test the tag modal:\n1. Click the 🏷️ icon\n2. Type to filter tags\n3. Use arrow keys to navigate"
    }
}

response = requests.post("http://localhost:8003/nodes/", json=note_data, headers=headers)
if response.status_code == 200:
    note = response.json()
    print(f"✓ Created note: {note['title']}")

print("\n" + "="*60)
print("TAG MODAL DEBUGGING INSTRUCTIONS:")
print("="*60)
print("1. Open the browser console (F12)")
print("2. Click on the note: '🔴 TEST TAG MODAL'")
print("3. Click the 🏷️ tag icon")
print("4. Look for console messages starting with 'searchForTags'")
print("5. Start typing in the search box")
print("6. Report what you see in the console:")
print("   - 'searchForTags called with query: ...'")
print("   - 'Available tags: ...'")
print("   - 'Suggestions found: ...'")
print("="*60)
print("\nIf you see NO console messages when typing:")
print("  → The oninput handler is not working")
print("\nIf you see console messages but no suggestions:")
print("  → The DOM update is not working")
print("="*60)