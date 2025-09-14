# File Upload API Guide

## Overview

The FastGTD API provides a dedicated endpoint for uploading files and attaching them to nodes as artifacts. This feature allows you to attach any type of file to tasks, notes, or other nodes in your GTD system.

## Prerequisites

Set your API base URL for consistency:
```bash
export API_BASE=http://127.0.0.1:8003  # If using start.sh
# OR
export API_BASE=http://127.0.0.1:8000  # If using uvicorn directly
```

## Endpoint

```
POST ${API_BASE}/artifacts
```

## Request Format

- **Method**: POST
- **Content-Type**: `multipart/form-data`
- **Authentication**: Bearer token required in Authorization header

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | File to upload (any type) |
| `node_id` | UUID | Yes | UUID of the node to attach the file to |

### File Processing

- **File Types**: Any file type is accepted (no restrictions)
- **File Size**: No enforced limit (handled by server configuration)
- **Encoding**: No encoding validation (files stored as-is)
- **Content**: Files can be empty

## Response Format

Returns an `ArtifactResponse` object with the created artifact details:

```json
{
  "id": "319eb663-c0a8-404d-b284-2cf630cff86e",
  "node_id": "0e212ca2-278d-4926-a24f-6f3b691eaf36",
  "filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf",
  "original_filename": "project_report.pdf",
  "mime_type": "application/pdf",
  "size_bytes": 1048576,
  "created_at": "2025-09-01T12:46:22.497374Z"
}
```

## Usage Examples

### Basic File Upload

```bash
curl -X POST "${API_BASE}/artifacts" \
  -H "Authorization: Bearer <your-access-token>" \
  -F "node_id=f015011d-f8b8-47c2-9300-7493691e6458" \
  -F "file=@my_document.pdf"
```

### Upload Multiple File Types

```bash
# Upload a PDF
curl -X POST "${API_BASE}/artifacts" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "node_id=f015011d-f8b8-47c2-9300-7493691e6458" \
  -F "file=@report.pdf"

# Upload an image
curl -X POST "${API_BASE}/artifacts" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "node_id=f015011d-f8b8-47c2-9300-7493691e6458" \
  -F "file=@screenshot.png"

# Upload a text file
curl -X POST "${API_BASE}/artifacts" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "node_id=f015011d-f8b8-47c2-9300-7493691e6458" \
  -F "file=@notes.txt"
```

### JavaScript/Fetch Example

```javascript
const formData = new FormData();
formData.append('node_id', 'f015011d-f8b8-47c2-9300-7493691e6458');
formData.append('file', fileInput.files[0]);

const response = await fetch(`${API_BASE}/artifacts`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});

const result = await response.json();
console.log('Created artifact:', result);
```

### Python Requests Example

```python
import requests

url = f'{API_BASE}/artifacts'
headers = {
    'Authorization': f'Bearer {access_token}'
}

with open('my_document.pdf', 'rb') as f:
    files = {'file': f}
    data = {'node_id': 'f015011d-f8b8-47c2-9300-7493691e6458'}

    response = requests.post(url, headers=headers, files=files, data=data)
    result = response.json()
    print(f"Created artifact: {result['id']}")
```

## Related Endpoints

### Download Artifact

```
GET ${API_BASE}/artifacts/{artifact_id}/download
```

Download the file associated with an artifact:

```bash
curl -X GET "${API_BASE}/artifacts/319eb663-c0a8-404d-b284-2cf630cff86e/download" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -o downloaded_file
```

### List Node Artifacts

```
GET ${API_BASE}/artifacts/node/{node_id}
```

Get all artifacts attached to a specific node:

```bash
curl -X GET "${API_BASE}/artifacts/node/f015011d-f8b8-47c2-9300-7493691e6458" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Response:
```json
{
  "artifacts": [
    {
      "id": "319eb663-c0a8-404d-b284-2cf630cff86e",
      "node_id": "f015011d-f8b8-47c2-9300-7493691e6458",
      "filename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf",
      "original_filename": "project_report.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 1048576,
      "created_at": "2025-09-01T12:46:22.497374Z"
    }
  ],
  "total": 1
}
```

### Delete Artifact

```
DELETE ${API_BASE}/artifacts/{artifact_id}
```

Delete an artifact and its associated file:

```bash
curl -X DELETE "${API_BASE}/artifacts/319eb663-c0a8-404d-b284-2cf630cff86e" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Error Responses

### Node Not Found
```json
{
  "detail": "Node not found"
}
```

### Authentication Error
```json
{
  "detail": "invalid_token"
}
```

### File Upload Error
```json
{
  "detail": "Failed to upload file: [error details]"
}
```

### File Not Found (Download)
```json
{
  "detail": "File not found on disk"
}
```

## File Storage

- Files are stored on the server filesystem
- Original filenames are preserved in the database
- Files are given unique filenames (UUID + original extension) to prevent conflicts
- File paths are managed internally and not exposed to clients

## Security Considerations

- **Authentication Required**: All endpoints require a valid Bearer token
- **User Isolation**: Users can only access artifacts attached to their own nodes
- **File Access Control**: Download permissions are validated through node ownership
- **No File Type Restrictions**: Accept any file type (consider implementing restrictions if needed)

## Performance Notes

- Files are stored directly to disk during upload
- Large files are handled synchronously (consider async processing for very large files)
- No built-in file size limits (controlled by server configuration)

## Bulk Upload Workflow

For uploading multiple files to the same node:

```bash
# Upload multiple files to the same node
for file in *.pdf; do
  curl -X POST "${API_BASE}/artifacts" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -F "node_id=f015011d-f8b8-47c2-9300-7493691e6458" \
    -F "file=@$file"
  echo "Uploaded: $file"
done
```

This approach allows for better error handling and progress tracking for each individual file upload.