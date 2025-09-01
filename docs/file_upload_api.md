# File Upload API Guide

## Overview

The FastGTD API provides a dedicated endpoint for uploading markdown files and automatically creating note records in the database. This feature simplifies the process of importing markdown content without manually crafting JSON payloads.

## Endpoint

```
POST /nodes/upload-file
```

## Request Format

- **Method**: POST
- **Content-Type**: `multipart/form-data`
- **Authentication**: Bearer token required in Authorization header

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Markdown file (.md extension) to upload |
| `parent_id` | UUID | No | UUID of parent folder/node |
| `title` | String | No | Custom title for the note (defaults to filename without extension) |

### File Validation Rules

- **File Extension**: Only `.md` files are accepted
- **File Size**: Maximum 10MB per file
- **Encoding**: Must be UTF-8 encoded
- **Content**: File cannot be empty (whitespace-only files are rejected)

## Response Format

Returns a standard `NoteResponse` object with the created note details:

```json
{
  "id": "319eb663-c0a8-404d-b284-2cf630cff86e",
  "owner_id": "0e212ca2-278d-4926-a24f-6f3b691eaf36",
  "parent_id": null,
  "node_type": "note",
  "title": "Test Upload Note",
  "sort_order": 0,
  "created_at": "2025-09-01T12:46:22.497374Z",
  "updated_at": "2025-09-01T12:46:22.497374Z",
  "is_list": false,
  "children_count": 0,
  "tags": [],
  "note_data": {
    "body": "# Test Markdown Note\n\nThis is a **test markdown note** for the file upload feature.\n\n## Features Tested\n\n- File upload endpoint\n- Markdown content parsing\n- Note creation from file"
  }
}
```

## Usage Examples

### Basic Upload with Custom Title

```bash
curl -X POST http://localhost:8001/nodes/upload-file \
  -H "Authorization: Bearer <your-access-token>" \
  -F "file=@my_notes.md" \
  -F "title=My Important Notes"
```

### Upload to Specific Parent Folder

```bash
curl -X POST http://localhost:8001/nodes/upload-file \
  -H "Authorization: Bearer <your-access-token>" \
  -F "file=@brainstorming.md" \
  -F "parent_id=f015011d-f8b8-47c2-9300-7493691e6458" \
  -F "title=Project Brainstorming Session"
```

### Upload with Auto-Generated Title

```bash
curl -X POST http://localhost:8001/nodes/upload-file \
  -H "Authorization: Bearer <your-access-token>" \
  -F "file=@meeting_notes_2025_01_15.md"
```

*Note: This will create a note with title "Meeting Notes 2025 01 15" (auto-generated from filename)*

### JavaScript/Fetch Example

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('title', 'My Uploaded Note');
formData.append('parent_id', 'f015011d-f8b8-47c2-9300-7493691e6458');

const response = await fetch('/nodes/upload-file', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});

const result = await response.json();
console.log('Created note:', result);
```

### Python Requests Example

```python
import requests

url = 'http://localhost:8001/nodes/upload-file'
headers = {
    'Authorization': f'Bearer {access_token}'
}

with open('my_notes.md', 'rb') as f:
    files = {'file': f}
    data = {
        'title': 'My Uploaded Notes',
        'parent_id': 'f015011d-f8b8-47c2-9300-7493691e6458'
    }
    
    response = requests.post(url, headers=headers, files=files, data=data)
    result = response.json()
    print(f"Created note: {result['id']}")
```

## Error Responses

### Invalid File Type
```json
{
  "detail": "Only .md files are supported"
}
```

### File Too Large
```json
{
  "detail": "File size too large (max 10MB)"
}
```

### Empty File
```json
{
  "detail": "File cannot be empty"
}
```

### Invalid Encoding
```json
{
  "detail": "File must be UTF-8 encoded"
}
```

### Parent Not Found
```json
{
  "detail": "Parent node not found"
}
```

### Authentication Error
```json
{
  "detail": "invalid_token"
}
```

## Title Generation

When no custom title is provided, the system automatically generates one from the filename:

- Removes the `.md` extension
- Replaces underscores (`_`) and hyphens (`-`) with spaces
- Applies title case formatting

**Examples:**
- `meeting_notes.md` → "Meeting Notes"
- `project-brainstorming.md` → "Project Brainstorming" 
- `quick-thoughts.md` → "Quick Thoughts"

## Integration Notes

- The uploaded file content becomes the `body` field of the created note
- All markdown formatting is preserved exactly as uploaded
- The created note follows the same structure as notes created via the standard `/nodes/` endpoint
- Parent-child relationships work the same way as with manually created notes
- The note can be updated, moved, tagged, and deleted using standard node operations

## Security Considerations

- Authentication is required - the note will be owned by the authenticated user
- File size limits prevent abuse (10MB maximum)
- Only markdown files are accepted to prevent malicious file uploads
- UTF-8 encoding validation prevents encoding-based attacks
- Parent node validation ensures users can only upload to folders they own

## Performance Notes

- Files are read into memory during processing
- Large files (approaching the 10MB limit) may take longer to process
- Consider implementing async processing for bulk uploads if needed

## Bulk Upload Workflow

For uploading multiple files, make separate requests for each file:

```bash
# Upload multiple files to the same parent
for file in *.md; do
  curl -X POST http://localhost:8001/nodes/upload-file \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -F "file=@$file" \
    -F "parent_id=f015011d-f8b8-47c2-9300-7493691e6458"
done
```

This approach allows for better error handling and progress tracking compared to a single bulk endpoint.