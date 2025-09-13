from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
import os

from app.core.config import get_settings
from app.db.session import get_engine
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.nodes import router as nodes_router
from app.api.settings import router as settings_router
from app.api.rules import router as rules_router
# Legacy API routers - disabled during migration
# from app.api.lists import router as lists_router
# from app.api.note_lists import router as note_lists_router
# from app.api.tasks import router as tasks_router
from app.api.tags import router as tags_router
# from app.api.tag_lists import router as taglists_router
# from app.api.notes import router as notes_router
from app.api.artifacts import router as artifacts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Optional: check DB connectivity on startup
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:  # Leave startup resilient; health endpoint will still show issues
        pass
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    # CORS: explicit origins are required when credentials are allowed
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173", 
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "https://50063c5d21b1.ngrok-free.app",  # Frontend ngrok URL
            "*",  # Allow all origins for mobile testing
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Mount templates directory for template system
    app.mount("/templates", StaticFiles(directory="templates"), name="templates")
    
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(nodes_router)
    app.include_router(settings_router, prefix="/settings", tags=["settings"])
    app.include_router(tags_router)
    app.include_router(rules_router)
    app.include_router(artifacts_router, prefix="/artifacts", tags=["artifacts"])
    # AI router - now fixed to use unified node system
    try:
        from app.api.ai import router as ai_router
        app.include_router(ai_router, prefix="/ai", tags=["ai"])
        print("✅ AI router enabled")
    except Exception as e:
        # Keep the app functional even if AI deps/config are missing
        print(f"⚠️  AI router disabled: {e}")
    
    # Mobile interface
    @app.get("/mobile")
    async def mobile_interface():
        return FileResponse("mobile_debug.html")
    
    # Desktop interface - serve same mobile interface for now
    @app.get("/desktop")
    async def desktop_interface():
        return FileResponse("mobile_debug.html")
    
    # Legacy API routers - disabled during migration
    # app.include_router(lists_router)
    # app.include_router(note_lists_router)
    # app.include_router(tasks_router)
    # app.include_router(taglists_router)
    # app.include_router(tags_router)
    # app.include_router(notes_router)
    # app.include_router(artifacts_router)
    # (AI router is enabled above if available)
    return app


app = create_app()
