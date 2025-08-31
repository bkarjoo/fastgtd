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

# Create multiple tags for testing
print("\n=== Creating test tags ===")
tag_names = ["urgent", "work", "personal", "review", "idea", "meeting", "project-alpha", "project-beta"]

# Get tag list first
response = requests.get("http://localhost:8003/tag-lists/", headers=headers)
if response.status_code == 200:
    tag_lists = response.json()
    if tag_lists:
        tag_list_id = tag_lists[0]['id']
        
        for tag_name in tag_names:
            # Check if tag already exists
            check_response = requests.get(f"http://localhost:8003/tags/", headers=headers)
            if check_response.status_code == 200:
                existing_tags = check_response.json()
                if not any(t['name'] == tag_name for t in existing_tags):
                    # Create tag
                    tag_data = {
                        "name": tag_name,
                        "tag_list_id": tag_list_id
                    }
                    create_response = requests.post("http://localhost:8003/tags/", json=tag_data, headers=headers)
                    if create_response.status_code == 200:
                        print(f"✓ Created tag: {tag_name}")
                    else:
                        print(f"✗ Failed to create tag {tag_name}: {create_response.status_code}")
                else:
                    print(f"✓ Tag already exists: {tag_name}")

print("\n" + "="*50)
print("TAG MODAL TEST INSTRUCTIONS:")
print("="*50)
print("1. Click the 🏷️ tag icon in any view")
print("2. The modal should show WITHOUT 'Manage Tags' title")
print("3. Current tags section should show WITHOUT 'Current Tags' label")
print("4. The search box should show available tags immediately")
print("5. As you type, tags should filter in real-time")
print("6. Use ↑↓ arrows to navigate suggestions")
print("7. Press Enter to select highlighted tag")
print("8. Click on any tag to add it")
print("="*50)