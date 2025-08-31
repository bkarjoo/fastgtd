#!/usr/bin/env python3
"""
Verify that smart folder rules are saved correctly
"""
import requests
import json

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

# Get all nodes
response = requests.get("http://localhost:8003/nodes/", headers=headers)
if response.status_code == 200:
    nodes = response.json()
    
    # Find our test smart folders
    test_folders = [n for n in nodes if n.get('title', '').startswith('TEST_SF_')]
    test_folders.sort(key=lambda x: x.get('title', ''))
    
    print("=== SMART FOLDER RULES VERIFICATION ===\n")
    
    for sf in test_folders:
        print(f"📁 {sf['title']}")
        
        # Get the full node details
        detail_response = requests.get(f"http://localhost:8003/nodes/{sf['id']}", headers=headers)
        if detail_response.status_code == 200:
            details = detail_response.json()
            
            if 'smart_folder_data' in details:
                rules = details['smart_folder_data'].get('rules', {})
                logic = rules.get('logic', 'NONE')
                conditions = rules.get('conditions', [])
                
                print(f"   Logic: {logic}")
                print(f"   Conditions: {len(conditions)}")
                
                for i, cond in enumerate(conditions, 1):
                    print(f"     {i}. Type: {cond.get('type')}")
                    print(f"        Operator: {cond.get('operator')}")
                    print(f"        Values: {cond.get('values')}")
            else:
                print("   ❌ NO RULES DATA FOUND")
                
            # Also get the contents to verify filtering
            contents_response = requests.get(f"http://localhost:8003/nodes/{sf['id']}/contents", headers=headers)
            if contents_response.status_code == 200:
                contents = contents_response.json()
                print(f"   Results: {len(contents)} items")
                if len(contents) <= 5:
                    for item in contents:
                        print(f"     - {item['title']} ({item['node_type']})")
        print()
    
    print("\n=== EXPECTED vs ACTUAL ===")
    print("TEST_SF_1_ALL_TYPES: Should have 1 condition (node_type in [task, note])")
    print("TEST_SF_2_TASKS_ONLY: Should have 1 condition (node_type in [task])")
    print("TEST_SF_3_EMPTY: Should have 1 condition (title_contains 'IMPOSSIBLE_STRING_XYZ123')")
    print("TEST_SF_4_HIGH_PRIORITY: Should have 2 conditions (node_type + task_priority)")
    print("TEST_SF_5_INCOMPLETE: Should have 2 conditions (node_type + task_status)")
else:
    print("Failed to get nodes")