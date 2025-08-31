#!/usr/bin/env python3
"""
Test that smart folder filtering actually works
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

# Create a few test items
print("\n=== Creating Test Data ===")

# Create a task
task_data = {
    "node_type": "task",
    "title": "Test Task for Filtering",
    "parent_id": None,
    "sort_order": 100,
    "task_data": {
        "status": "todo",
        "priority": "high"
    }
}
response = requests.post("http://localhost:8003/nodes/", json=task_data, headers=headers)
if response.status_code == 200:
    print("✓ Created task")
else:
    print(f"❌ Failed to create task: {response.status_code}")

# Create a note
note_data = {
    "node_type": "note",
    "title": "Test Note (should not appear in task filter)",
    "parent_id": None,
    "sort_order": 101,
    "note_data": {
        "body": "This is a test note"
    }
}
response = requests.post("http://localhost:8003/nodes/", json=note_data, headers=headers)
if response.status_code == 200:
    print("✓ Created note")
else:
    print(f"❌ Failed to create note: {response.status_code}")

# Now check the "All Tasks" smart folder
print("\n=== Checking Smart Folder Filtering ===")

# Find the "All Tasks" smart folder
response = requests.get("http://localhost:8003/nodes/", headers=headers)
if response.status_code == 200:
    nodes = response.json()
    all_tasks_folder = next((n for n in nodes if n.get('title') == '📋 All Tasks'), None)
    
    if all_tasks_folder:
        # Get its contents
        contents_response = requests.get(f"http://localhost:8003/nodes/{all_tasks_folder['id']}/contents", headers=headers)
        if contents_response.status_code == 200:
            contents = contents_response.json()
            print(f"✓ Smart folder '📋 All Tasks' has {len(contents)} items")
            
            # Check what's in it
            task_count = sum(1 for item in contents if item.get('node_type') == 'task')
            note_count = sum(1 for item in contents if item.get('node_type') == 'note')
            
            print(f"  - Tasks: {task_count}")
            print(f"  - Notes: {note_count}")
            
            if task_count > 0 and note_count == 0:
                print("✅ Filtering works! Only tasks are shown")
            else:
                print("❌ Filtering issue - notes shouldn't appear in task filter")
                
            # List the items
            for item in contents[:5]:  # Show first 5
                print(f"    • {item['title']} ({item['node_type']})")
        else:
            print(f"❌ Failed to get contents: {contents_response.status_code}")
    else:
        print("❌ Could not find 'All Tasks' smart folder")

print("\n📱 Check in UI:")
print("1. Navigate to the '📋 All Tasks' smart folder")
print("2. Verify you see tasks but NOT notes")