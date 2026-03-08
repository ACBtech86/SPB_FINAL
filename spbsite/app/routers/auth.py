from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from passlib.hash import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.templates_config import templates
from spb_shared.models import User

router = APIRouter(tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request, "error": None})


@router.post("/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")

    result = await db.execute(
        select(User).where(User.username == username, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()

    if not user or not bcrypt.verify(password, user.password_hash):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Usuario ou senha invalidos."},
            status_code=401,
        )

    request.session["user_id"] = user.id
    request.session["username"] = user.username
    return RedirectResponse(url="/monitoring/control/local", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
