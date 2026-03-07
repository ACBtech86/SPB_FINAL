from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.dependencies import AuthRequired
from app.routers import auth, logs, messages, monitoring, queue, viewer

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title=settings.app_title)

# Session middleware for cookie-based auth
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

# Static files
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Jinja2 templates (shared instance)
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.exception_handler(AuthRequired)
async def auth_required_handler(request: Request, exc: AuthRequired):
    return RedirectResponse(url="/login", status_code=303)


@app.get("/")
async def root():
    return RedirectResponse(url="/monitoring/control/local", status_code=303)


# Register routers
app.include_router(auth.router)
app.include_router(monitoring.router)
app.include_router(messages.router)
app.include_router(queue.router)
app.include_router(logs.router)
app.include_router(viewer.router)
