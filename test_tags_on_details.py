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

# Test 1: Create a folder
print("\n=== Test 1: Create folder ===")
folder_data = {
    "node_type": "folder",
    "title": "Test Folder with Tags",
    "parent_id": None,
    "sort_order": 100
}

response = requests.post("http://localhost:8003/nodes/", json=folder_data, headers=headers)
if response.status_code == 200:
    folder = response.json()
    print(f"✓ Created folder: {folder['title']} (id: {folder['id']})")
    folder_id = folder['id']
else:
    print(f"✗ Failed to create folder: {response.status_code}")
    exit(1)

# Test 2: Create a task
print("\n=== Test 2: Create task ===")
task_data = {
    "node_type": "task",
    "title": "Test Task with Tags",
    "parent_id": None,
    "sort_order": 200,
    "task_data": {
        "status": "todo",
        "priority": "high"
    }
}

response = requests.post("http://localhost:8003/nodes/", json=task_data, headers=headers)
if response.status_code == 200:
    task = response.json()
    print(f"✓ Created task: {task['title']} (id: {task['id']})")
    task_id = task['id']
else:
    print(f"✗ Failed to create task: {response.status_code}")
    exit(1)

# Test 3: Create tags
print("\n=== Test 3: Create tags ===")
tag_names = ["important", "work", "project-x"]
tag_ids = []

# First, get existing tags
response = requests.get("http://localhost:8003/tags/", headers=headers)
existing_tags = {}
if response.status_code == 200:
    for tag in response.json():
        existing_tags[tag['name']] = tag['id']
    print(f"  Found {len(existing_tags)} existing tags")

for tag_name in tag_names:
    if tag_name in existing_tags:
        print(f"✓ Using existing tag: {tag_name} (id: {existing_tags[tag_name]})")
        tag_ids.append(existing_tags[tag_name])
    else:
        # Create tag using query parameters
        response = requests.post(f"http://localhost:8003/tags/?name={tag_name}", headers=headers)
        if response.status_code in [200, 201]:  # 201 is created status
            tag = response.json()
            print(f"✓ Created tag: {tag['name']} (id: {tag['id']})")
            tag_ids.append(tag['id'])
        else:
            print(f"✗ Failed to create tag {tag_name}: {response.status_code}")
            print(f"  Response: {response.text}")

# Test 4: Add tags to folder
print("\n=== Test 4: Add tags to folder ===")
for i, tag_id in enumerate(tag_ids[:2]):  # Add first 2 tags to folder
    response = requests.post(f"http://localhost:8003/nodes/{folder_id}/tags/{tag_id}", headers=headers)
    if response.status_code in [200, 201]:  # 201 is created status
        print(f"✓ Added tag '{tag_names[i]}' to folder")
    else:
        print(f"✗ Failed to add tag: {response.status_code}")

# Test 5: Add tags to task
print("\n=== Test 5: Add tags to task ===")
for i, tag_id in enumerate(tag_ids[1:], 1):  # Add last 2 tags to task
    response = requests.post(f"http://localhost:8003/nodes/{task_id}/tags/{tag_id}", headers=headers)
    if response.status_code in [200, 201]:  # 201 is created status
        print(f"✓ Added tag '{tag_names[i]}' to task")
    else:
        print(f"✗ Failed to add tag: {response.status_code}")

# Test 6: Get folder with tags
print("\n=== Test 6: Get folder with tags ===")
response = requests.get(f"http://localhost:8003/nodes/{folder_id}", headers=headers)
if response.status_code == 200:
    folder = response.json()
    print(f"✓ Retrieved folder: {folder['title']}")
    if 'tags' in folder and folder['tags']:
        print(f"  Tags: {', '.join([tag['name'] for tag in folder['tags']])}")
    else:
        print(f"  No tags found")
else:
    print(f"✗ Failed to get folder: {response.status_code}")

# Test 7: Get task with tags
print("\n=== Test 7: Get task with tags ===")
response = requests.get(f"http://localhost:8003/nodes/{task_id}", headers=headers)
if response.status_code == 200:
    task = response.json()
    print(f"✓ Retrieved task: {task['title']}")
    if 'tags' in task and task['tags']:
        print(f"  Tags: {', '.join([tag['name'] for tag in task['tags']])}")
    else:
        print(f"  No tags found")
else:
    print(f"✗ Failed to get task: {response.status_code}")

print("\n✅ Tag display tests completed!")
print("\n📱 Now navigate to the details page of these nodes in the UI to see the tags displayed with delete buttons")