#!/usr/bin/env python3
"""
Test that smart folders show 'No results' instead of 'This folder is empty'
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

# Get all nodes to find smart folders
response = requests.get("http://localhost:8003/nodes/", headers=headers)
if response.status_code == 200:
    nodes = response.json()
    smart_folders = [n for n in nodes if n.get('node_type') == 'smart_folder']
    print(f"✓ Found {len(smart_folders)} smart folders")
    
    for sf in smart_folders:
        print(f"\n📁 Smart Folder: '{sf['title']}' (ID: {sf['id']})")
        
        # Get contents
        contents_response = requests.get(f"http://localhost:8003/nodes/{sf['id']}/contents", headers=headers)
        if contents_response.status_code == 200:
            contents = contents_response.json()
            if len(contents) == 0:
                print(f"  → Empty smart folder (should show 'No results' in UI)")
            else:
                print(f"  → Has {len(contents)} results")
        
        # Check if it has rules defined
        if 'smart_folder_data' in sf:
            rules = sf.get('smart_folder_data', {}).get('rules', {})
            conditions = rules.get('conditions', [])
            if conditions:
                print(f"  → Has {len(conditions)} filter conditions")
            else:
                print(f"  → No filter conditions defined")

print("\n📱 Now check the UI:")
print("1. Navigate to http://localhost:8003/mobile")
print("2. Click on any smart folder")
print("3. Verify it shows 'No results' instead of 'This folder is empty'")