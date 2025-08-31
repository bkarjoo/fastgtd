#!/usr/bin/env python3
"""
Test that smart folders show 'No results' for empty filters
"""
import requests

# Login
login_response = requests.post("http://localhost:8003/auth/login", json={
    "email": "test@example.com",
    "password": "test123"
})

if login_response.status_code != 200:
    print(f"❌ Login failed")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ Logged in")

# Create a smart folder with an impossible filter (to guarantee no results)
print("\n=== Creating Smart Folder with No Possible Results ===")
smart_folder_data = {
    "node_type": "smart_folder",
    "title": "🔍 Empty Results Test",
    "parent_id": None,
    "sort_order": 2,
    "smart_folder_data": {
        "rules": {
            "logic": "AND",
            "conditions": [
                {
                    "type": "title_contains",
                    "operator": "contains",
                    "values": ["XYZABC123IMPOSSIBLE"]  # This should match nothing
                }
            ]
        }
    }
}

response = requests.post("http://localhost:8003/nodes/", json=smart_folder_data, headers=headers)
if response.status_code == 200:
    sf = response.json()
    print(f"✓ Created smart folder: {sf['title']}")
    
    # Get contents (should be empty)
    contents_response = requests.get(f"http://localhost:8003/nodes/{sf['id']}/contents", headers=headers)
    if contents_response.status_code == 200:
        contents = contents_response.json()
        if len(contents) == 0:
            print("✓ Smart folder correctly returns 0 results")
            print("\n✅ SUCCESS: Backend filtering works correctly")
            print("\n📱 MANUAL UI TEST REQUIRED:")
            print("1. Go to http://localhost:8003/mobile")
            print("2. Click on '🔍 Empty Results Test' smart folder")
            print("3. VERIFY: You should see 'No results' NOT 'This folder is empty'")
        else:
            print(f"❌ Unexpected: Got {len(contents)} results")
else:
    print(f"❌ Failed to create smart folder: {response.status_code}")
    print(response.text)