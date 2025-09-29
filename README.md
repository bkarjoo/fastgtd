
# FastGTD

This is a GTD (Getting Things Done) application built with FastAPI and React.

## Development Setup

### Prerequisites
- Python 3.8+
- PostgreSQL database running
- Node.js (for build tools)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fastgtd
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy the sample environment file: `cp .env.sample .env`
   - Edit `.env` and update the values for your environment:
     - Set your PostgreSQL connection string in `DATABASE_URL`
     - Change `JWT_SECRET` to a secure random string for production
   - Ensure PostgreSQL is running and create a database for the application

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend server**
   ```bash
   # Using default port
   uvicorn app.main:app --reload

   # Or using the included startup script (port 8003)
   ./start.sh
   ```

### Frontend Access

Set your API base URL for consistency across documentation:
```bash
export API_BASE=http://localhost:8003  # If using start.sh
# OR
export API_BASE=http://localhost:8000  # If using uvicorn directly
```

The frontend is a mobile web application served by the backend. After starting the backend server, access it at:

- **Main mobile interface**: `${API_BASE}/mobile`
- **Desktop interface**: `${API_BASE}/desktop`

### Build Tools (Optional)

For static asset building and testing:

```bash
npm install
npm run build  # Build static assets
```

## Architecture

### Core Data Model

FastGTD uses a flexible polymorphic node-based architecture where all items (tasks, notes, folders, templates, smart folders) inherit from a base `Node` class. This design provides:

- **Unified hierarchy**: All items can be organized in a tree structure
- **Type-specific attributes**: Each node type extends the base with specialized fields
- **Polymorphic queries**: Efficient loading of mixed node types in a single query

#### Node Types

- **Task**: Action items with status, priority, due dates, and recurrence
- **Note**: Text content with rich formatting support
- **Folder**: Containers for organizing other nodes
- **SmartFolder**: Dynamic folders with rule-based filtering
- **Template**: Reusable blueprints for creating structured content hierarchies

### Recent Performance & Quality Improvements

#### Performance Optimizations (Jan 2025)

The API layer has been significantly optimized to eliminate N+1 query problems:

- **Batch Loading**: Implemented efficient batch loading for node conversions
  - Reduced database queries from O(n) to O(1) for bulk operations
  - Children counts, tags, and type-specific data loaded in batched queries
  - 10-100x performance improvement for list endpoints with many items

- **Smart Caching**: Preload and cache related data for common access patterns

#### Schema Validation Improvements

- **Type-Safe APIs**: All endpoints now use properly typed Pydantic models
- **Field Validation**: Comprehensive validation moved to schema layer
  - Color hex codes validated with regex patterns
  - Required fields enforced at schema level
  - Better error messages for invalid input

#### SmartFolder Migration Strategy

SmartFolder rules are transitioning from inline JSON to reusable `Rule` entities:

- **Backward Compatible**: Legacy `rules` field still supported with deprecation warnings
- **New Approach**: Use `rule_id` to reference standalone Rule entities
- **Migration Tools**: Utilities in `app/services/smart_folder_migration.py` to help migrate
- **Benefits**: Reusable rules, better organization, cleaner API

See `docs/smart_folder_migration.md` for migration guide.

## API Documentation

### Authentication

All API endpoints (except `/health` and `/auth/*`) require JWT authentication:

```bash
# Sign up
curl -X POST ${API_BASE}/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass"}'

# Login to get token
curl -X POST ${API_BASE}/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass"}'

# Use token in requests
curl -H "Authorization: Bearer YOUR_TOKEN" ${API_BASE}/nodes
```

### Key Endpoints

- `GET /nodes` - List all nodes with filtering and pagination (uses batch loading)
- `POST /nodes` - Create a new node (task, note, folder, etc.)
- `GET /nodes/{id}` - Get a specific node with all related data
- `PUT /nodes/{id}` - Update a node
- `DELETE /nodes/{id}` - Delete a node and its children

- `GET /tags` - List all tags
- `POST /tags` - Create or find a tag (with color validation)
- `POST /nodes/{id}/tags/{tag_id}` - Attach a tag to a node

- `GET /templates` - List templates (batch loaded)
- `POST /templates/{id}/instantiate` - Create nodes from template

- `GET /{smart_folder_id}/contents` - Get smart folder filtered results (batch loaded)
- `POST /smart-folders/preview` - Preview smart folder rules

### OpenAPI Documentation

Interactive API documentation available at:
- Swagger UI: `${API_BASE}/docs`
- ReDoc: `${API_BASE}/redoc`

## Testing

Run the test suite:

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/api/test_nodes.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

Current test status: **80/80 tests passing** ✅

## Development Guidelines

### Code Quality

- **Type Safety**: Use Pydantic models for all API request/response bodies
- **Validation**: Put validation logic in schemas, not endpoints
- **Performance**: Use batch loading for operations returning multiple items
- **Testing**: Maintain test coverage for all new features

### Database Migrations

Create and apply migrations using Alembic:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

## MVC Design

The application follows an MVC (Model-View-Controller) design pattern with a React frontend and FastAPI backend.

### Model

SQLAlchemy models in `app/models/` define the database structure with proper relationships and constraints.

### View

React components provide the user interface (mobile and desktop views).

### Controller

FastAPI endpoints in `app/api/` handle business logic and coordinate between models and services.
