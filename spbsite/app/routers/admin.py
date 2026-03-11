"""Admin routes for managing profiles and users."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from passlib.context import CryptContext
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.templates_config import templates
from spb_shared.models import User, Profile, ProfileMessagePermission, SPBMensagem

router = APIRouter(prefix="/admin", tags=["admin"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/profiles", response_class=HTMLResponse)
async def list_profiles(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all user profiles."""
    result = await db.execute(
        select(Profile).order_by(Profile.name)
    )
    profiles = list(result.scalars().all())

    return templates.TemplateResponse(
        "admin/profiles.html",
        {"request": request, "user": user, "profiles": profiles},
    )


@router.get("/profiles/{profile_id}", response_class=HTMLResponse)
async def edit_profile(
    request: Request,
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Edit profile and its message permissions."""
    # Get profile with permissions
    result = await db.execute(
        select(Profile)
        .options(selectinload(Profile.message_permissions))
        .where(Profile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        return RedirectResponse(url="/admin/profiles", status_code=303)

    # Get all available messages
    result = await db.execute(select(SPBMensagem).order_by(SPBMensagem.msg_id))
    all_messages = list(result.scalars().all())

    # Get message IDs that this profile has access to
    allowed_msg_ids = {perm.msg_id for perm in profile.message_permissions}

    return templates.TemplateResponse(
        "admin/profile_edit.html",
        {
            "request": request,
            "user": user,
            "profile": profile,
            "all_messages": all_messages,
            "allowed_msg_ids": allowed_msg_ids,
        },
    )


@router.post("/profiles/{profile_id}/permissions")
async def update_profile_permissions(
    request: Request,
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update message permissions for a profile."""
    form = await request.form()
    selected_msg_ids = form.getlist("msg_ids")

    # Delete existing permissions
    await db.execute(
        delete(ProfileMessagePermission).where(
            ProfileMessagePermission.profile_id == profile_id
        )
    )

    # Add new permissions
    for msg_id in selected_msg_ids:
        permission = ProfileMessagePermission(
            profile_id=profile_id,
            msg_id=msg_id
        )
        db.add(permission)

    await db.commit()

    return RedirectResponse(
        url=f"/admin/profiles/{profile_id}?success=1",
        status_code=303
    )


@router.get("/profiles/new", response_class=HTMLResponse)
async def new_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create new profile form."""
    # Get all available messages
    result = await db.execute(select(SPBMensagem).order_by(SPBMensagem.msg_id))
    all_messages = list(result.scalars().all())

    return templates.TemplateResponse(
        "admin/profile_new.html",
        {
            "request": request,
            "user": user,
            "all_messages": all_messages,
        },
    )


@router.post("/profiles/create")
async def create_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new profile."""
    form = await request.form()
    name = form.get("name", "").strip()
    description = form.get("description", "").strip()
    selected_msg_ids = form.getlist("msg_ids")

    if not name:
        return RedirectResponse(url="/admin/profiles/new?error=name_required", status_code=303)

    # Create profile
    new_profile = Profile(
        name=name,
        description=description if description else None,
        is_active=True
    )
    db.add(new_profile)
    await db.flush()  # Get the profile ID

    # Add permissions
    for msg_id in selected_msg_ids:
        permission = ProfileMessagePermission(
            profile_id=new_profile.id,
            msg_id=msg_id
        )
        db.add(permission)

    await db.commit()

    return RedirectResponse(url="/admin/profiles?success=created", status_code=303)


@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all users."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.profile))
        .order_by(User.username)
    )
    users = list(result.scalars().all())

    # Get all profiles for the form
    result = await db.execute(select(Profile).order_by(Profile.name))
    profiles = list(result.scalars().all())

    return templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "user": user, "users": users, "profiles": profiles},
    )


@router.post("/users/{user_id}/profile")
async def update_user_profile(
    request: Request,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user's profile assignment."""
    form = await request.form()
    profile_id = form.get("profile_id")

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        return RedirectResponse(url="/admin/users?error=user_not_found", status_code=303)

    # Update profile
    target_user.profile_id = int(profile_id) if profile_id and profile_id != "" else None
    await db.commit()

    return RedirectResponse(url="/admin/users?success=updated", status_code=303)


@router.get("/users/new", response_class=HTMLResponse)
async def new_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create new user form."""
    result = await db.execute(select(Profile).order_by(Profile.name))
    profiles = list(result.scalars().all())

    return templates.TemplateResponse(
        "admin/user_new.html",
        {"request": request, "user": user, "profiles": profiles},
    )


@router.post("/users/create")
async def create_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new user."""
    form = await request.form()
    username = form.get("username", "").strip()
    password = form.get("password", "").strip()
    profile_id = form.get("profile_id")

    if not username or not password:
        return RedirectResponse(
            url="/admin/users/new?error=fields_required",
            status_code=303
        )

    # Check if username already exists
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none():
        return RedirectResponse(
            url="/admin/users/new?error=username_exists",
            status_code=303
        )

    # Create user
    password_hash = pwd_context.hash(password)
    new_user = User(
        username=username,
        password_hash=password_hash,
        profile_id=int(profile_id) if profile_id and profile_id != "" else None,
        is_active=True
    )
    db.add(new_user)
    await db.commit()

    return RedirectResponse(url="/admin/users?success=created", status_code=303)


@router.get("/api/profiles/{profile_id}/messages")
async def get_profile_messages(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """API endpoint to get allowed messages for a profile."""
    result = await db.execute(
        select(ProfileMessagePermission.msg_id)
        .where(ProfileMessagePermission.profile_id == profile_id)
    )
    msg_ids = [row[0] for row in result.all()]

    return JSONResponse(content={"msg_ids": msg_ids})
