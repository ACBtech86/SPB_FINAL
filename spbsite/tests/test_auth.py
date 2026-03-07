"""Tests for authentication routes — Section 1 (14 tests).

Covers: login page rendering, login validation, session/logout, root redirect.
"""

from passlib.hash import bcrypt


# ---------------------------------------------------------------------------
# 1.1 Login Page Rendering
# ---------------------------------------------------------------------------

async def test_login_page_renders(client):
    """#1 — GET /login returns 200 and contains 'Finvest DTVM SPB'."""
    response = await client.get("/login")
    assert response.status_code == 200
    assert "Finvest DTVM SPB" in response.text


async def test_login_page_accessible_when_logged_in(authenticated_client):
    """#2 — GET /login when already logged in still returns 200."""
    response = await authenticated_client.get("/login")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 1.2 Login Validation
# ---------------------------------------------------------------------------

async def test_login_valid_credentials(client, admin_user):
    """#3 — POST /login with valid credentials → 303 redirect to /monitoring/control/local."""
    response = await client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/monitoring/control/local" in response.headers.get("location", "")


async def test_login_wrong_password(client, admin_user):
    """#4 — POST /login with wrong password → 401, shows error message."""
    response = await client.post(
        "/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert "Usuario ou senha invalidos" in response.text


async def test_login_nonexistent_username(client):
    """#5 — POST /login with nonexistent username → 401."""
    response = await client.post(
        "/login",
        data={"username": "nonexistent", "password": "whatever"},
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert "Usuario ou senha invalidos" in response.text


async def test_login_empty_username(client):
    """#6 — POST /login with empty username → 401."""
    response = await client.post(
        "/login",
        data={"username": "", "password": "anything"},
        follow_redirects=False,
    )
    assert response.status_code == 401


async def test_login_empty_password(client, admin_user):
    """#7 — POST /login with empty password → 401."""
    response = await client.post(
        "/login",
        data={"username": "admin", "password": ""},
        follow_redirects=False,
    )
    assert response.status_code == 401


async def test_login_inactive_user(client, inactive_user):
    """#8 — POST /login with inactive user → 401."""
    response = await client.post(
        "/login",
        data={"username": "disabled", "password": "disabled"},
        follow_redirects=False,
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 1.3 Session & Logout
# ---------------------------------------------------------------------------

async def test_logout_redirects(authenticated_client):
    """#9 — GET /logout → 303 redirect to /login, session cleared."""
    response = await authenticated_client.get("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers.get("location", "")


async def test_protected_route_without_session(client):
    """#10 — Access protected route without session → 303 redirect to /login."""
    response = await client.get("/monitoring/control/local", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers.get("location", "")


async def test_protected_route_invalid_user_id(client, db_session):
    """#11 — Access protected route with deactivated user → redirect to /login."""
    from spb_shared.models import User
    user = User(username="temp", password_hash=bcrypt.hash("temp"), is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    await client.post(
        "/login",
        data={"username": "temp", "password": "temp"},
        follow_redirects=False,
    )

    # Deactivate the user to simulate invalid session
    user.is_active = False
    await db_session.commit()

    response = await client.get("/monitoring/control/local", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers.get("location", "")


async def test_protected_route_deleted_user(client, db_session):
    """#12 — Access protected route with deleted user → redirect to /login."""
    from spb_shared.models import User
    user = User(username="toremove", password_hash=bcrypt.hash("toremove"), is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    await client.post(
        "/login",
        data={"username": "toremove", "password": "toremove"},
        follow_redirects=False,
    )

    # Delete the user
    await db_session.delete(user)
    await db_session.commit()

    response = await client.get("/monitoring/control/local", follow_redirects=False)
    assert response.status_code == 303
    assert "/login" in response.headers.get("location", "")


# ---------------------------------------------------------------------------
# 1.4 Root Redirect
# ---------------------------------------------------------------------------

async def test_root_unauthenticated(client):
    """#13 — GET / unauthenticated → redirect chain ending at /login."""
    response = await client.get("/", follow_redirects=False)
    assert response.status_code == 303
    # Root redirects to /monitoring/control/local which then redirects to /login
    location = response.headers.get("location", "")
    assert "/monitoring" in location or "/login" in location


async def test_root_authenticated(authenticated_client):
    """#14 — GET / authenticated → 303 redirect to /monitoring/control/local."""
    response = await authenticated_client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert "/monitoring/control/local" in response.headers.get("location", "")
