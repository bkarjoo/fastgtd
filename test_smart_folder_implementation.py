#!/usr/bin/env python3
"""
Test script to verify the smart folder implementation works end-to-end.
This script will:
1. Create test data (tasks with different statuses, priorities, and dates)
2. Create a smart folder with specific rules
3. Test the filtering functionality
4. Verify results appear correctly
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
API_BASE = "http://localhost:8003"
LOGIN_DATA = {
    "email": "test@example.com",
    "password": "test123"
}

def login():
    """Login and get access token"""
    response = requests.post(f"{API_BASE}/auth/login", json=LOGIN_DATA)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✓ Logged in successfully")
        return token
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(response.text)
        exit(1)

def create_test_data(token):
    """Create test nodes for smart folder filtering"""
    headers = {"Authorization": f"Bearer {token}"}
    created_nodes = []
    
    # Create a parent folder
    folder_data = {
        "node_type": "folder", 
        "title": "Smart Folder Test Container",
        "parent_id": None,
        "sort_order": 1
    }
    response = requests.post(f"{API_BASE}/nodes/", json=folder_data, headers=headers)
    if response.status_code == 200:
        folder = response.json()
        created_nodes.append(folder)
        print(f"✓ Created folder: {folder['title']}")
        folder_id = folder['id']
    else:
        print(f"✗ Failed to create folder: {response.status_code}")
        return []
    
    # Create test tasks with different properties
    test_tasks = [
        {
            "title": "High Priority Todo Task",
            "status": "todo",
            "priority": "high",
            "due_at": (datetime.now() + timedelta(days=7)).isoformat(),
            "parent_id": folder_id
        },
        {
            "title": "In Progress Medium Task", 
            "status": "in_progress",
            "priority": "medium", 
            "due_at": (datetime.now() + timedelta(days=3)).isoformat(),
            "parent_id": folder_id
        },
        {
            "title": "Completed Low Priority Task",
            "status": "done",
            "priority": "low",
            "due_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "parent_id": folder_id
        },
        {
            "title": "Urgent Task with Early Start",
            "status": "todo",
            "priority": "urgent",
            "earliest_start_at": (datetime.now() + timedelta(days=1)).isoformat(),
            "parent_id": folder_id
        }
    ]
    
    for task_info in test_tasks:
        task_data = {
            "node_type": "task",
            "title": task_info["title"],
            "parent_id": task_info["parent_id"],
            "sort_order": 100,
            "task_data": {
                "status": task_info["status"],
                "priority": task_info["priority"],
                "due_at": task_info.get("due_at"),
                "earliest_start_at": task_info.get("earliest_start_at")
            }
        }
        
        response = requests.post(f"{API_BASE}/nodes/", json=task_data, headers=headers)
        if response.status_code == 200:
            task = response.json()
            created_nodes.append(task)
            print(f"✓ Created task: {task['title']}")
        else:
            print(f"✗ Failed to create task '{task_info['title']}': {response.status_code}")
    
    # Create test notes
    note_data = {
        "node_type": "note",
        "title": "Test Note for Filtering",
        "parent_id": folder_id,
        "sort_order": 200,
        "note_data": {
            "body": "This is a test note for smart folder filtering."
        }
    }
    
    response = requests.post(f"{API_BASE}/nodes/", json=note_data, headers=headers)
    if response.status_code == 200:
        note = response.json()
        created_nodes.append(note)
        print(f"✓ Created note: {note['title']}")
    else:
        print(f"✗ Failed to create note: {response.status_code}")
    
    return created_nodes

def create_smart_folder(token):
    """Create a smart folder with filtering rules"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Smart folder rules: Find all high priority tasks
    rules = {
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
                "values": ["high", "urgent"]
            }
        ]
    }
    
    smart_folder_data = {
        "node_type": "smart_folder",
        "title": "🔍 High Priority Tasks",
        "parent_id": None,
        "sort_order": 10,
        "smart_folder_data": {
            "rules": rules,
            "auto_refresh": True
        }
    }
    
    response = requests.post(f"{API_BASE}/nodes/", json=smart_folder_data, headers=headers)
    if response.status_code == 200:
        smart_folder = response.json()
        print(f"✓ Created smart folder: {smart_folder['title']}")
        return smart_folder
    else:
        print(f"✗ Failed to create smart folder: {response.status_code}")
        print(response.text)
        return None

def test_smart_folder_contents(token, smart_folder_id):
    """Test that smart folder returns filtered results"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\\n=== Testing Smart Folder Contents ===")
    response = requests.get(f"{API_BASE}/nodes/{smart_folder_id}/contents", headers=headers)
    
    if response.status_code == 200:
        contents = response.json()
        print(f"✓ Smart folder returned {len(contents)} results")
        
        for item in contents:
            print(f"  - {item['title']} ({item['node_type']})")
            if item['node_type'] == 'task' and 'task_data' in item:
                task_data = item['task_data']
                print(f"    Status: {task_data.get('status', 'N/A')}, Priority: {task_data.get('priority', 'N/A')}")
        
        # Verify results match our filter criteria
        expected_results = 2  # Should find "High Priority Todo Task" and "Urgent Task with Early Start"
        if len(contents) == expected_results:
            print(f"✓ Smart folder correctly filtered results ({len(contents)} high/urgent priority tasks)")
        else:
            print(f"⚠ Expected {expected_results} results, got {len(contents)}")
            
        return True
    else:
        print(f"✗ Failed to get smart folder contents: {response.status_code}")
        print(response.text)
        return False

def test_preview_functionality(token):
    """Test the smart folder preview API"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\\n=== Testing Preview Functionality ===")
    
    # Test rules: All tasks that are not completed
    preview_rules = {
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
    
    response = requests.post(f"{API_BASE}/nodes/smart_folder/preview", 
                           json=preview_rules, headers=headers)
    
    if response.status_code == 200:
        results = response.json()
        print(f"✓ Preview returned {len(results)} incomplete tasks")
        
        for task in results:
            print(f"  - {task['title']} (Status: {task.get('task_data', {}).get('status', 'N/A')})")
        
        # Should find 3 incomplete tasks (todo and in_progress, but not done)
        expected_count = 3
        if len(results) == expected_count:
            print(f"✓ Preview correctly filtered incomplete tasks")
        else:
            print(f"⚠ Expected {expected_count} incomplete tasks, got {len(results)}")
            
        return True
    else:
        print(f"✗ Preview failed: {response.status_code}")
        print(response.text)
        return False

def main():
    print("🚀 Testing Smart Folder Implementation")
    print("=" * 50)
    
    # Step 1: Login
    token = login()
    
    # Step 2: Create test data
    print(f"\\n=== Creating Test Data ===")
    created_nodes = create_test_data(token)
    if not created_nodes:
        print("Failed to create test data, aborting")
        return
    
    # Step 3: Create smart folder
    print(f"\\n=== Creating Smart Folder ===")
    smart_folder = create_smart_folder(token)
    if not smart_folder:
        print("Failed to create smart folder, aborting")
        return
    
    # Step 4: Test smart folder filtering
    success = test_smart_folder_contents(token, smart_folder['id'])
    
    # Step 5: Test preview functionality
    preview_success = test_preview_functionality(token)
    
    # Summary
    print(f"\\n" + "=" * 50)
    if success and preview_success:
        print("✅ All smart folder tests PASSED!")
        print("\\n📝 Manual testing steps:")
        print("1. Navigate to the web interface")
        print("2. Click on the '🔍 High Priority Tasks' smart folder")  
        print("3. Verify it shows 'No results' when empty instead of 'This folder is empty'")
        print("4. Click on a task and verify breadcrumbs show the original parent")
        print("5. Edit the smart folder and test the rules editor interface")
        print("6. Use the preview functionality to test different filter combinations")
    else:
        print("❌ Some tests failed - check the output above")

if __name__ == "__main__":
    main()