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
    print(login_response.text)
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Test 1: Create a folder using the new folder type
print("\n=== Test 1: Create folder with new 'folder' type ===")
folder_data = {
    "node_type": "folder",
    "title": "Test Folder (Pure)",
    "parent_id": None,
    "sort_order": 100
}

response = requests.post("http://localhost:8003/nodes/", json=folder_data, headers=headers)
if response.status_code == 200:
    folder = response.json()
    print(f"✓ Created folder: {folder['title']} (id: {folder['id']})")
    print(f"  Node type: {folder['node_type']}")
    folder_id = folder['id']
else:
    print(f"✗ Failed to create folder: {response.status_code}")
    print(response.text)
    exit(1)

# Test 2: Create a child folder
print("\n=== Test 2: Create child folder ===")
child_data = {
    "node_type": "folder",
    "title": "Child Folder",
    "parent_id": folder_id,
    "sort_order": 10
}

response = requests.post("http://localhost:8003/nodes/", json=child_data, headers=headers)
if response.status_code == 200:
    child = response.json()
    print(f"✓ Created child folder: {child['title']}")
    child_id = child['id']
else:
    print(f"✗ Failed to create child: {response.status_code}")
    print(response.text)

# Test 3: Create a task in the folder
print("\n=== Test 3: Create task in folder ===")
task_data = {
    "node_type": "task",
    "title": "Task in Folder",
    "parent_id": folder_id,
    "sort_order": 20,
    "task_data": {
        "status": "todo",
        "priority": "medium"
    }
}

response = requests.post("http://localhost:8003/nodes/", json=task_data, headers=headers)
if response.status_code == 200:
    task = response.json()
    print(f"✓ Created task in folder: {task['title']}")
    task_id = task['id']
else:
    print(f"✗ Failed to create task: {response.status_code}")
    print(response.text)

# Test 4: Get folder details
print("\n=== Test 4: Get folder details ===")
response = requests.get(f"http://localhost:8003/nodes/{folder_id}", headers=headers)
if response.status_code == 200:
    folder = response.json()
    print(f"✓ Retrieved folder: {folder['title']}")
    print(f"  Type: {folder['node_type']}")
    print(f"  Is list: {folder.get('is_list', False)}")
    print(f"  Children count: {folder.get('children_count', 0)}")
else:
    print(f"✗ Failed to get folder: {response.status_code}")

# Test 5: Move task to different folder
print("\n=== Test 5: Move task between folders ===")
move_data = {
    "node_id": task_id,
    "new_parent_id": child_id
}

response = requests.post("http://localhost:8003/nodes/move", json=move_data, headers=headers)
if response.status_code == 200:
    print(f"✓ Moved task to child folder")
else:
    print(f"✗ Failed to move task: {response.status_code}")

# Test 6: List all nodes to see structure
print("\n=== Test 6: List all nodes ===")
response = requests.get("http://localhost:8003/nodes/", headers=headers)
if response.status_code == 200:
    nodes = response.json()
    folders = [n for n in nodes if n['node_type'] == 'folder']
    print(f"✓ Found {len(folders)} folders (new type)")
    for f in folders[:5]:  # Show first 5
        print(f"  - {f['title']} (parent: {f.get('parent_id', 'root')})")
else:
    print(f"✗ Failed to list nodes: {response.status_code}")

print("\n✅ All folder API tests completed!")