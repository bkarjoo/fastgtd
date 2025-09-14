
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

## MVC Design

The application is being refactored to follow an MVC (Model-View-Controller) design pattern. The goal is to create a responsive React app with a unified shared-component front end.

### Model

The model is represented by the SQLAlchemy models in the `app/models` directory. These models define the structure of the data in the database.

### View

The view will be implemented using React components. The goal is to create a set of reusable components that can be shared across the application.

### Controller

The controller will be implemented as a set of services that handle the business logic of the application. These services will be called by the FastAPI endpoints.
