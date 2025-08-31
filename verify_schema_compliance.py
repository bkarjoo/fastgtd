#!/usr/bin/env python3
"""
Verify that our test smart folders follow the schema correctly
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

# Get a specific test smart folder
response = requests.get("http://localhost:8003/nodes/", headers=headers)
if response.status_code == 200:
    nodes = response.json()
    
    # Find TEST_SF_3_EMPTY
    test_folder = next((n for n in nodes if n.get('title') == 'TEST_SF_3_EMPTY'), None)
    
    if test_folder:
        print("Found TEST_SF_3_EMPTY")
        print(f"ID: {test_folder['id']}")
        
        # Check what's in the response
        print("\nFull node data from list endpoint:")
        print(json.dumps(test_folder, indent=2))
        
        # Now get it individually
        print("\n" + "="*50)
        individual_response = requests.get(f"http://localhost:8003/nodes/{test_folder['id']}", headers=headers)
        if individual_response.status_code == 200:
            individual_data = individual_response.json()
            print("Individual GET response:")
            print(json.dumps(individual_data, indent=2))
        else:
            print(f"Failed to get individual: {individual_response.status_code}")
    else:
        print("TEST_SF_3_EMPTY not found")