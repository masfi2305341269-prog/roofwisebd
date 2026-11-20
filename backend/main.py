from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.api import api_router
from app.database.database import engine, Base

# Enforce production security settings at startup.
# Raises RuntimeError with actionable guidance if any required setting is missing or insecure.
# This is a no-op in development (ENVIRONMENT != "production").
settings.validate_production_settings()

# Create SQLite database tables if not existing
Base.metadata.create_all(bind=engine)

def _ensure_sqlite_email_verification_schema():
    """Ensure email_verified column exists on users in local SQLite (preserving existing users)."""
    try:
        with engine.begin() as conn:
            res = conn.exec_driver_sql("PRAGMA table_info(users)").fetchall()
            col_names = [r[1] for r in res]
            if "email_verified" not in col_names:
                conn.exec_driver_sql("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 1 NOT NULL")
    except Exception:
        pass

_ensure_sqlite_email_verification_schema()

app = FastAPI(
    title=f"{settings.PROJECT_NAME} API",
    description=(
        "Backend REST API for RoofwiseBD — AI-Powered Rooftop Solar Assessment & Energy Recommendation "
        "Platform for Bangladesh. Incorporates BERC 2026 tariff schedule (June 4, 2026 revision) "
        "and SREDA Net Metering Guideline 2025 compliance."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware (Strict origins, never wildcard '*' when allow_credentials=True)
cors_kwargs = {
    "allow_origins": settings.BACKEND_CORS_ORIGINS,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    "allow_headers": ["*"],
}
if getattr(settings, "BACKEND_CORS_ORIGIN_REGEX", None):
    cors_kwargs["allow_origin_regex"] = settings.BACKEND_CORS_ORIGIN_REGEX

app.add_middleware(CORSMiddleware, **cors_kwargs)

# Mount Uploads directory for previewing uploaded bills and images
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

# Mount API v1 Routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", summary="Root Welcome Endpoint")
def root_info():
    return {
        "project": settings.PROJECT_NAME,
        "description": "AI-Powered Rooftop Solar Assessment & Recommendation Platform for Bangladesh",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_v1_prefix": settings.API_V1_STR,
        "status": "online"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
