
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

4. **Set up database**
   - Ensure PostgreSQL is running
   - Create a database for the application
   - Update database connection settings in your environment

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend server**
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Access

The frontend is a mobile web application served by the backend. After starting the backend server, access it at:

- **Main mobile interface**: `http://localhost:8000/mobile`
- **Desktop interface**: `http://localhost:8000/desktop` 
- **Test interface**: `http://localhost:8000/mobile-test`

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
