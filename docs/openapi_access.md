# OpenAPI Documentation Access

## Live OpenAPI Specification

The FastGTD API provides a live OpenAPI specification that is automatically generated from the current code. This ensures the documentation is always up-to-date with the actual API implementation.

## Accessing the OpenAPI Spec

### Set API Base URL

```bash
export API_BASE=http://127.0.0.1:8003  # If using start.sh
# OR
export API_BASE=http://127.0.0.1:8000  # If using uvicorn directly
```

### Get the OpenAPI JSON

```bash
curl "${API_BASE}/openapi.json"
```

### View Interactive Documentation

The FastAPI server automatically provides interactive API documentation:

- **Swagger UI**: `${API_BASE}/docs`
- **ReDoc**: `${API_BASE}/redoc`

## Generating Static OpenAPI File (Optional)

If you need to save the OpenAPI specification to a file:

```bash
# Generate and save OpenAPI spec
curl -s "${API_BASE}/openapi.json" > docs/openapi.json

# Pretty-print the JSON
curl -s "${API_BASE}/openapi.json" | python3 -m json.tool > docs/openapi.json
```

## Using the OpenAPI Spec

### With OpenAPI Generator

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate client SDK (example for TypeScript)
openapi-generator-cli generate \
  -i "${API_BASE}/openapi.json" \
  -g typescript-fetch \
  -o ./generated-client
```

### With Postman

1. Open Postman
2. Click "Import"
3. Choose "Link" and enter: `${API_BASE}/openapi.json`
4. Postman will create a collection with all API endpoints

### With curl

```bash
# Save spec to file for offline use
curl "${API_BASE}/openapi.json" -o api-spec.json

# Use tools like swagger-codegen, openapi-generator, etc.
```

## Current API Endpoints

The API includes the following main router groups:

- **Health**: `/health` - Service health check
- **Authentication**: `/auth/*` - User registration, login, token management
- **Nodes**: `/nodes/*` - Core GTD entities (tasks, notes, folders, smart folders, templates)
- **Tags**: `/tags/*` - Tag management and search
- **Rules**: `/rules/*` - Smart folder rules and automation
- **Settings**: `/settings/*` - User preferences and configuration
- **Artifacts**: `/artifacts/*` - File upload and attachment management
- **AI**: `/ai/*` - AI-powered features (optional, if enabled)

## Benefits of Live Documentation

- **Always Current**: Automatically reflects code changes
- **No Maintenance**: No need to manually update static files
- **Interactive**: Test endpoints directly from the browser
- **Version Consistency**: Guaranteed to match the running API version

## Development Workflow

1. **Start the server**: `./start.sh` or `uvicorn app.main:app --reload`
2. **Set API_BASE**: `export API_BASE=http://127.0.0.1:8003`
3. **Access docs**: Open `${API_BASE}/docs` in your browser
4. **Generate clients**: Use `${API_BASE}/openapi.json` with code generation tools