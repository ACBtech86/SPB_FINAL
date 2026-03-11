from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.dependencies import AuthRequired
from app.routers import admin, auth, logs, messages, monitoring, queue, viewer

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title=settings.app_title)

# Session middleware for cookie-based auth
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

# Static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.exception_handler(AuthRequired)
async def auth_required_handler(request: Request, exc: AuthRequired):
    return RedirectResponse(url="/login", status_code=303)


@app.get("/")
async def root():
    return RedirectResponse(url="/monitoring/control/local", status_code=303)


@app.get("/test-viewer-fix")
async def test_viewer_fix():
    """Test endpoint to verify viewer fix is working."""
    from app.database import async_session
    from app.services.monitoring import get_messages
    from app.templates_config import composite_key_filter

    async with async_session() as db:
        result = await get_messages(db, "inbound", "bacen", limit=2)

        rows_info = []
        for row in result['rows']:
            key = composite_key_filter(row)
            rows_info.append({
                "cod_msg": row.cod_msg,
                "composite_key": key,
                "viewer_url": f"/viewer/spb_bacen_to_local/{key}"
            })

        return {
            "status": "OK",
            "total_rows": len(result['rows']),
            "rows": rows_info,
            "message": "Viewer fix is working! Restart your browser or clear cache."
        }


# Register routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(monitoring.router)
app.include_router(messages.router)
app.include_router(queue.router)
app.include_router(logs.router)
app.include_router(viewer.router)
