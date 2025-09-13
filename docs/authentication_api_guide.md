# Authentication API Testing Guide - REVISED

## Critical Issue Discovery
During testing, we discovered that shell environment variables do not persist between separate `curl` commands in our testing environment. This guide has been completely rewritten to address this reality.

## Prerequisites

1. **Database Setup**
   - Ensure PostgreSQL is running
   - Database migrations are up to date: `alembic upgrade head`

2. **Server Running**
   - FastAPI server running on port 8001: `uvicorn app.main:app --reload --port 8001`

## WORKING Method: Complete Test in Single Session

### Step 1: Create Complete Test Script

Since environment variables don't persist between individual commands, you MUST use scripts or single compound commands.

Create `/tmp/complete_auth_test.sh`:
```bash
#!/bin/bash
set -e

echo "=== FastGTD Authentication Test ==="

# Step 1: Health Check
echo "1. Testing health endpoint..."
HEALTH=$(curl -s "http://127.0.0.1:8001/health")
echo "Health response: $HEALTH"

# Step 2: Create User (ignore error if exists)
echo -e "\n2. Creating test user..."
curl -s -X POST "http://127.0.0.1:8001/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "scripttestuser@example.com",
    "password": "testpass123",
    "full_name": "Script Test User"
  }' || echo "User may already exist"

# Step 3: Login and extract token
echo -e "\n3. Getting authentication token..."
curl -s -X POST "http://127.0.0.1:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "scripttestuser@example.com", "password": "testpass123"}' > /tmp/auth_response.json

# Extract token from response file
ACCESS_TOKEN=$(python3 -c "import json; print(json.load(open('/tmp/auth_response.json'))['access_token'])")
echo "Token obtained: ${ACCESS_TOKEN:0:30}..."

# Step 4: Test protected endpoint
echo -e "\n4. Testing protected endpoint..."
NODES_RESPONSE=$(curl -s -X GET "http://127.0.0.1:8001/nodes/" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo "Nodes response: $NODES_RESPONSE"

# Step 5: Create a test node
echo -e "\n5. Creating test node..."
NODE_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8001/nodes/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Node",
    "node_type": "task"
  }')
echo "Node creation response: $NODE_RESPONSE"

# Extract node ID for further testing
NODE_ID=$(echo $NODE_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['id']) if 'id' in data else print('ERROR')")
echo "Created node ID: $NODE_ID"

# Step 6: Read the created node
if [ "$NODE_ID" != "ERROR" ]; then
  echo -e "\n6. Reading created node..."
  READ_RESPONSE=$(curl -s -X GET "http://127.0.0.1:8001/nodes/$NODE_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  echo "Read response: $READ_RESPONSE"
  
  # Step 7: Delete the node
  echo -e "\n7. Deleting node..."
  DELETE_RESPONSE=$(curl -s -X DELETE "http://127.0.0.1:8001/nodes/$NODE_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  echo "Delete response status: $?"
  
  # Step 8: Verify node is gone
  echo -e "\n8. Verifying node deletion..."
  VERIFY_RESPONSE=$(curl -s -X GET "http://127.0.0.1:8001/nodes/$NODE_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  echo "Verification response: $VERIFY_RESPONSE"
fi

# Cleanup
rm -f /tmp/auth_response.json

echo -e "\n=== Test Complete ==="
```

### Step 2: Run Complete Test

```bash
# Make script executable
chmod +x /tmp/complete_auth_test.sh

# Run complete test
/tmp/complete_auth_test.sh
```

## Alternative: Manual Step-by-Step with File Method

If you prefer manual testing, use this file-based approach:

### Step 1: Login and Save Token
```bash
# Get login response
curl -s -X POST "http://127.0.0.1:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "testuser@example.com", "password": "testpass"}' > /tmp/auth.json

# Extract and save token
python3 -c "import json; print(json.load(open('/tmp/auth.json'))['access_token'])" > /tmp/token.txt

# Verify token was saved
head -c 50 /tmp/token.txt
```

### Step 2: Use Token in Subsequent Commands
```bash
# Test protected endpoint
curl -X GET "http://127.0.0.1:8001/nodes/" \
  -H "Authorization: Bearer $(cat /tmp/token.txt)"

# Create node
curl -X POST "http://127.0.0.1:8001/nodes/" \
  -H "Authorization: Bearer $(cat /tmp/token.txt)" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Node", "node_type": "task"}' > /tmp/node_response.json

# Extract node ID
python3 -c "import json; print(json.load(open('/tmp/node_response.json'))['id'])" > /tmp/node_id.txt

# Read node
curl -X GET "http://127.0.0.1:8001/nodes/$(cat /tmp/node_id.txt)" \
  -H "Authorization: Bearer $(cat /tmp/token.txt)"

# Delete node  
curl -X DELETE "http://127.0.0.1:8001/nodes/$(cat /tmp/node_id.txt)" \
  -H "Authorization: Bearer $(cat /tmp/token.txt)"

# Cleanup
rm -f /tmp/auth.json /tmp/token.txt /tmp/node_response.json /tmp/node_id.txt
```

## What DOESN'T Work (Lessons Learned)

### ❌ Environment Variables Between Commands
```bash
# THIS DOESN'T WORK - Variables don't persist
ACCESS_TOKEN=$(curl ... | python3 -c ...)
curl -H "Authorization: Bearer $ACCESS_TOKEN" ...  # TOKEN IS EMPTY
```

### ❌ Multi-line Variable Assignments  
```bash
# THIS CAUSES SHELL PARSING ERRORS
ACCESS_TOKEN=$(curl ... \
  -H "..." \
  -d "..." | python3 -c "...")
```

### ❌ Complex Pipe Chains in Variables
```bash
# THIS FAILS IN MANY SHELL ENVIRONMENTS  
TOKEN=$(curl ... | python3 ... | tr ...)
```

## Debugging Authentication Issues

### Check Server Logs
The FastAPI server logs show request status:
- `200 OK` = Success
- `401 Unauthorized` = Invalid/missing token
- `405 Method Not Allowed` = Wrong HTTP method

### Verify Token Format
A valid JWT has 3 parts separated by dots:
```bash
# Count dots in token (should be 2)
echo "TOKEN_HERE" | tr -cd '.' | wc -c
```

### Test Token Manually
Save token to file and test:
```bash
echo "YOUR_TOKEN_HERE" > /tmp/test_token.txt
curl -v -X GET "http://127.0.0.1:8001/nodes/" \
  -H "Authorization: Bearer $(cat /tmp/test_token.txt)"
```

## API Endpoints Reference

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/health` | No | Health check |
| POST | `/auth/signup` | No | Create account |
| POST | `/auth/login` | No | Get access token |
| GET | `/nodes/` | Yes | List nodes |
| POST | `/nodes/` | Yes | Create node |
| GET | `/nodes/{id}` | Yes | Read node |
| DELETE | `/nodes/{id}` | Yes | Delete node |

---

## Final Testing Certification - REVISED

**Date:** September 6, 2025 (REVISED)  
**Issue:** Original documentation contained fundamental flaws regarding shell environment variable persistence  
**Resolution:** Complete rewrite with file-based and script-based approaches

### Root Cause Analysis
The authentication system works correctly. The issue was documentation that assumed shell environment variables persist between separate command executions, which they don't in our testing environment.

### Verified Working Methods
1. **✅ Complete Script Approach** - Single script that maintains variables throughout execution
2. **✅ File-based Token Storage** - Saving tokens to files and reading them in subsequent commands  
3. **✅ Manual Copy-Paste** - Manually copying tokens between commands

### What Actually Works
- JWT token generation and validation ✅
- Protected endpoint authorization ✅  
- User registration and login ✅
- Node CRUD operations ✅

**Status: ✅ AUTHENTICATION SYSTEM VERIFIED - DOCUMENTATION CORRECTED**

The authentication system is fully functional. Previous issues were due to incorrect documentation assumptions about shell behavior.