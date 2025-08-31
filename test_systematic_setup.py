#!/usr/bin/env python3
"""
Systematic test setup for smart folders
Creates precise test data and provides exact test instructions
"""
import requests
import json
from datetime import datetime, timedelta

# Login
print("Setting up systematic test data...")
login_response = requests.post("http://localhost:8003/auth/login", json={
    "email": "test@example.com",
    "password": "test123"
})

if login_response.status_code != 200:
    print(f"❌ Login failed")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ Logged in\n")

# Clean up old test smart folders first
print("=== Cleaning up old test data ===")
response = requests.get("http://localhost:8003/nodes/", headers=headers)
if response.status_code == 200:
    nodes = response.json()
    test_folders = [n for n in nodes if n.get('title', '').startswith('TEST_')]
    for folder in test_folders:
        del_response = requests.delete(f"http://localhost:8003/nodes/{folder['id']}", headers=headers)
        if del_response.status_code == 200:
            print(f"  Deleted: {folder['title']}")

print("\n=== Creating Test Data ===")

# Create parent folder for organization
parent_folder = {
    "node_type": "folder",
    "title": "TEST_DATA_CONTAINER",
    "parent_id": None,
    "sort_order": 1000
}
response = requests.post("http://localhost:8003/nodes/", json=parent_folder, headers=headers)
if response.status_code == 200:
    container = response.json()
    container_id = container['id']
    print(f"✓ Created container: {container['title']}")
else:
    print("❌ Failed to create container")
    exit(1)

# Create exactly 3 tasks with specific properties
tasks_created = []

# Task 1: High priority, todo
task1 = {
    "node_type": "task",
    "title": "TEST_TASK_HIGH_TODO",
    "parent_id": container_id,
    "sort_order": 1,
    "task_data": {
        "status": "todo",
        "priority": "high"
    }
}
response = requests.post("http://localhost:8003/nodes/", json=task1, headers=headers)
if response.status_code == 200:
    tasks_created.append(response.json())
    print(f"✓ Created: TEST_TASK_HIGH_TODO (high priority, todo)")

# Task 2: Low priority, done
task2 = {
    "node_type": "task",
    "title": "TEST_TASK_LOW_DONE",
    "parent_id": container_id,
    "sort_order": 2,
    "task_data": {
        "status": "done",
        "priority": "low"
    }
}
response = requests.post("http://localhost:8003/nodes/", json=task2, headers=headers)
if response.status_code == 200:
    tasks_created.append(response.json())
    print(f"✓ Created: TEST_TASK_LOW_DONE (low priority, done)")

# Task 3: Medium priority, in_progress
task3 = {
    "node_type": "task",
    "title": "TEST_TASK_MEDIUM_PROGRESS",
    "parent_id": container_id,
    "sort_order": 3,
    "task_data": {
        "status": "in_progress",
        "priority": "medium"
    }
}
response = requests.post("http://localhost:8003/nodes/", json=task3, headers=headers)
if response.status_code == 200:
    tasks_created.append(response.json())
    print(f"✓ Created: TEST_TASK_MEDIUM_PROGRESS (medium priority, in_progress)")

# Create exactly 1 note
note1 = {
    "node_type": "note",
    "title": "TEST_NOTE_ONE",
    "parent_id": container_id,
    "sort_order": 4,
    "note_data": {
        "body": "This is a test note"
    }
}
response = requests.post("http://localhost:8003/nodes/", json=note1, headers=headers)
if response.status_code == 200:
    print(f"✓ Created: TEST_NOTE_ONE (note)")

print(f"\n=== Test Data Summary ===")
print(f"Container: TEST_DATA_CONTAINER")
print(f"  - 3 tasks (1 todo, 1 done, 1 in_progress)")
print(f"  - 1 note")

print(f"\n=== Creating Test Smart Folders ===")

# TEST CASE 1: Smart folder that shows ALL items (should return 4 items)
sf1 = {
    "node_type": "smart_folder",
    "title": "TEST_SF_1_ALL_TYPES",
    "parent_id": None,
    "sort_order": 2001,
    "smart_folder_data": {
        "rules": {
            "logic": "OR",
            "conditions": [
                {
                    "type": "node_type",
                    "operator": "in",
                    "values": ["task", "note"]
                }
            ]
        }
    }
}
response = requests.post("http://localhost:8003/nodes/", json=sf1, headers=headers)
if response.status_code == 200:
    sf1_id = response.json()['id']
    print(f"✓ TEST_SF_1_ALL_TYPES - Should show 4+ items (all tasks and notes)")

# TEST CASE 2: Smart folder that shows ONLY TASKS (should return 3 tasks)
sf2 = {
    "node_type": "smart_folder",
    "title": "TEST_SF_2_TASKS_ONLY",
    "parent_id": None,
    "sort_order": 2002,
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
response = requests.post("http://localhost:8003/nodes/", json=sf2, headers=headers)
if response.status_code == 200:
    sf2_id = response.json()['id']
    print(f"✓ TEST_SF_2_TASKS_ONLY - Should show 3+ tasks only")

# TEST CASE 3: Smart folder with IMPOSSIBLE filter (should return 0 items)
sf3 = {
    "node_type": "smart_folder",
    "title": "TEST_SF_3_EMPTY",
    "parent_id": None,
    "sort_order": 2003,
    "smart_folder_data": {
        "rules": {
            "logic": "AND",
            "conditions": [
                {
                    "type": "title_contains",
                    "operator": "contains",
                    "values": ["IMPOSSIBLE_STRING_XYZ123"]
                }
            ]
        }
    }
}
response = requests.post("http://localhost:8003/nodes/", json=sf3, headers=headers)
if response.status_code == 200:
    sf3_id = response.json()['id']
    print(f"✓ TEST_SF_3_EMPTY - Should show 'No results'")

# TEST CASE 4: Smart folder for HIGH PRIORITY tasks only (should return 1 task)
sf4 = {
    "node_type": "smart_folder",
    "title": "TEST_SF_4_HIGH_PRIORITY",
    "parent_id": None,
    "sort_order": 2004,
    "smart_folder_data": {
        "rules": {
            "logic": "AND",
            "conditions": [
                {
                    "type": "node_type",
                    "operator": "in",
                    "values": ["task"]
                },
                {
                    "type": "task_priority",
                    "operator": "in",
                    "values": ["high"]
                }
            ]
        }
    }
}
response = requests.post("http://localhost:8003/nodes/", json=sf4, headers=headers)
if response.status_code == 200:
    sf4_id = response.json()['id']
    print(f"✓ TEST_SF_4_HIGH_PRIORITY - Should show 1 task (TEST_TASK_HIGH_TODO)")

# TEST CASE 5: Smart folder for INCOMPLETE tasks (todo + in_progress)
sf5 = {
    "node_type": "smart_folder",
    "title": "TEST_SF_5_INCOMPLETE",
    "parent_id": None,
    "sort_order": 2005,
    "smart_folder_data": {
        "rules": {
            "logic": "AND",
            "conditions": [
                {
                    "type": "node_type",
                    "operator": "in",
                    "values": ["task"]
                },
                {
                    "type": "task_status",
                    "operator": "in",
                    "values": ["todo", "in_progress"]
                }
            ]
        }
    }
}
response = requests.post("http://localhost:8003/nodes/", json=sf5, headers=headers)
if response.status_code == 200:
    sf5_id = response.json()['id']
    print(f"✓ TEST_SF_5_INCOMPLETE - Should show 2 tasks (todo + in_progress)")

print("\n" + "="*60)
print("📋 MANUAL TEST INSTRUCTIONS")
print("="*60)
print("\nGo to http://localhost:8003/mobile and test IN THIS ORDER:\n")

print("\n1️⃣ TEST CASE 1: Basic 'No Results' Message")
print("   - Click on 'TEST_SF_3_EMPTY'")
print("   - ✓ PASS if: Shows 'No results'")
print("   - ✗ FAIL if: Shows 'This folder is empty' or anything else\n")

print("2️⃣ TEST CASE 2: Simple Filter Works")
print("   - Click on 'TEST_SF_2_TASKS_ONLY'")
print("   - ✓ PASS if: Shows at least 3 tasks")
print("   - ✓ PASS if: Does NOT show TEST_NOTE_ONE")
print("   - ✗ FAIL if: Shows any notes\n")

print("3️⃣ TEST CASE 3: Two-Condition Filter (AND logic)")
print("   - Click on 'TEST_SF_4_HIGH_PRIORITY'")
print("   - ✓ PASS if: Shows exactly TEST_TASK_HIGH_TODO")
print("   - ✗ FAIL if: Shows other tasks or is empty\n")

print("4️⃣ TEST CASE 4: Status Filter")
print("   - Click on 'TEST_SF_5_INCOMPLETE'")
print("   - ✓ PASS if: Shows TEST_TASK_HIGH_TODO and TEST_TASK_MEDIUM_PROGRESS")
print("   - ✓ PASS if: Does NOT show TEST_TASK_LOW_DONE")
print("   - ✗ FAIL if: Shows completed task or wrong count\n")

print("5️⃣ TEST CASE 5: Breadcrumb Display")
print("   - In any TEST_SF folder with results")
print("   - Look at any TEST_TASK item")
print("   - ✓ PASS if: Shows 'TEST_DATA_CONTAINER' as breadcrumb under title")
print("   - ✗ FAIL if: No breadcrumb visible\n")

print("="*60)
print("Report which test cases PASS or FAIL")
print("="*60)