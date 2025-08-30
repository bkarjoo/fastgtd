#!/usr/bin/env python3
import requests
import json

# First, let's login to get a token
login_data = {
    "email": "test@example.com",
    "password": "test123"
}

# Try to login
login_response = requests.post("http://localhost:8003/auth/login", json=login_data)
if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"Got token: {token[:20]}...")
else:
    print(f"Login failed with status {login_response.status_code}")
    print(login_response.text)
    # Try to create a test user
    signup_data = {
        "email": "test@example.com",
        "password": "test123",
        "full_name": "Test User"
    }
    signup_response = requests.post("http://localhost:8003/auth/signup", json=signup_data)
    if signup_response.status_code == 201:
        print("Created test user, trying login again...")
        login_response = requests.post("http://localhost:8003/auth/login", json=login_data)
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            print(f"Got token: {token[:20]}...")
        else:
            print("Still can't login")
            exit(1)
    else:
        print(f"Signup failed: {signup_response.text}")
        exit(1)

# Now test the nodes endpoint
headers = {"Authorization": f"Bearer {token}"}

# Test 1: Simple GET request
print("\n=== Test 1: GET /nodes/ ===")
response = requests.get("http://localhost:8003/nodes/", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")
else:
    print(f"Success! Got {len(response.json())} nodes")

# Test 2: GET with parent_id parameter (as string, which might cause 422)
print("\n=== Test 2: GET /nodes/ with parent_id as string ===")
response = requests.get("http://localhost:8003/nodes/?parent_id=invalid-uuid", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")

# Test 3: GET with parent_id=null (which might be the issue)
print("\n=== Test 3: GET /nodes/ with parent_id=null ===")
response = requests.get("http://localhost:8003/nodes/?parent_id=null", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")

# Test 4: GET with parent_id= (empty string)
print("\n=== Test 4: GET /nodes/ with parent_id= (empty) ===")
response = requests.get("http://localhost:8003/nodes/?parent_id=", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text}")