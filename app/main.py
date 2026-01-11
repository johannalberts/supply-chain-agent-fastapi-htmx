from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin
from app.config import get_settings
from app.database import engine, create_db_and_tables
from app.routes import auth, dashboard, api
from app.admin import UserAdmin, TaskStatusAdmin, ReportAdmin

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(api.router, tags=["api"])

# Setup SQLAdmin
admin = Admin(app, engine, title="Supply Chain Admin")
admin.add_view(UserAdmin)
admin.add_view(TaskStatusAdmin)
admin.add_view(ReportAdmin)


@app.on_event("startup")
def on_startup():
    """Create database tables on startup"""
    create_db_and_tables()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
