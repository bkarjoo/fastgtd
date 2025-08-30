# Fix 422 error when frontend sends invalid parent_id parameter

## Bug Description
The frontend is sending invalid `parent_id` query parameters to the `/nodes/` endpoint, causing 422 Unprocessable Entity errors.

## Current Behavior
- Frontend sometimes sends `parent_id=null` (string "null") or `parent_id=` (empty string)
- API correctly rejects these as invalid UUIDs with 422 error
- Error message: "Input should be a valid UUID"

## Expected Behavior
- When `parent_id` is null or empty, it should be omitted from query parameters entirely
- Only valid UUIDs should be sent as `parent_id` parameter

## Root Cause
The frontend code is incorrectly constructing query parameters, including null/empty values as strings instead of omitting them.

## Reproduction Steps
1. Load the application
2. Check browser console for 422 errors on nodes endpoint
3. Inspect network tab to see requests with `?parent_id=null` or `?parent_id=`

## Test Script
A test script has been created at `test_nodes_endpoint.py` that demonstrates the issue:
```python
# Test with invalid parent_id values shows 422 errors:
GET /nodes/?parent_id=null -> 422
GET /nodes/?parent_id= -> 422
GET /nodes/?parent_id=invalid-uuid -> 422
```

## Solution
Update frontend code to:
- Only include `parent_id` in query string when it has a valid UUID value
- Omit the parameter entirely when null or empty
- Review all places where query parameters are dynamically constructed

## Affected Files
- Frontend code that constructs URLs with query parameters
- Possibly in dynamically constructed API calls
- Check for URLSearchParams usage or string concatenation with query params

## Priority
Medium - API is working correctly but frontend errors affect user experience

## Additional Notes
- The basic `loadNodes()` function in `/static/js/nodes.js` works correctly (no query params)
- Issue likely in code that dynamically builds query strings
- Server-side validation is working as intended