#!/usr/bin/env python3
"""
Test creating a smart folder with simple rules
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

# Create a smart folder with a simple rule: only show tasks
print("\n=== Creating Smart Folder with Rules ===")
smart_folder_data = {
    "node_type": "smart_folder",
    "title": "📋 All Tasks",
    "parent_id": None,
    "sort_order": 5,
    "smart_folder_data": {
        "rules": {
            "logic": "AND",
            "conditions": [
                {
                    "type": "node_type",
                    "operator": "in",
                    "values": ["task"]
                }
            ]
        }
    }
}

response = requests.post("http://localhost:8003/nodes/", json=smart_folder_data, headers=headers)
if response.status_code == 200:
    sf = response.json()
    print(f"✓ Created smart folder: {sf['title']}")
    print(f"  ID: {sf['id']}")
    
    # Try to get the smart folder back and verify rules were saved
    get_response = requests.get(f"http://localhost:8003/nodes/{sf['id']}", headers=headers)
    if get_response.status_code == 200:
        retrieved = get_response.json()
        if 'smart_folder_data' in retrieved:
            rules = retrieved['smart_folder_data'].get('rules', {})
            if rules.get('conditions'):
                print(f"✓ Rules were saved correctly")
                print(f"  Logic: {rules.get('logic')}")
                print(f"  Conditions: {len(rules.get('conditions', []))} defined")
            else:
                print(f"❌ Rules were not saved")
else:
    print(f"❌ Failed to create smart folder: {response.status_code}")
    print(response.text)

print("\n📱 Test in UI:")
print("1. Go to http://localhost:8003/mobile")
print("2. Click on '📋 All Tasks' smart folder")
print("3. Click the edit button")
print("4. Verify the rules editor appears with the condition already set")