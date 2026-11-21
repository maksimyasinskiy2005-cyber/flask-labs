from sqlalchemy import select
from app import db
from app.models import User


# =====================================================================
# 1. Views Tests: перевірка завантаження сторінок реєстрації та входу
# =====================================================================
def test_register_page_loads(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Register" in response.data or "Реєстрація".encode("utf-8") in response.data


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data or "ВХІД".encode("utf-8") in response.data


# =====================================================================
# 2. Тестування збереження користувача у БД при реєстрації та валідації
# =====================================================================
def test_user_registration_saves_hashed_password(app, client):
    response = client.post(
        "/register",
        data={
            "username": "yulia12",
            "email": "yulia12@gmail.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=False,
    )
    # Після успішної реєстрації відбувається перенаправлення на сторінку входу
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with app.app_context():
        user = db.session.scalar(select(User).where(User.email == "yulia12@gmail.com"))
        assert user is not None
        assert user.username == "yulia12"
        assert user.password != "password123"
        assert user.password.startswith("$2b$")
        assert user.check_password("password123") is True


def test_duplicate_email_registration_fails(app, client, registered_user):
    response = client.post(
        "/register",
        data={
            "username": "newuser1",
            "email": registered_user["email"],
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "вже існує".encode("utf-8") in response.data


# =====================================================================
# 3. Тестування входу, доступу до захищених маршрутів і виходу
# =====================================================================
def test_protected_routes_redirect_anonymous_user(client):
    resp_account = client.get("/account", follow_redirects=False)
    assert resp_account.status_code == 302
    assert "/login" in resp_account.headers["Location"]

    resp_users = client.get("/users", follow_redirects=False)
    assert resp_users.status_code == 302
    assert "/login" in resp_users.headers["Location"]


def test_login_and_logout_flow(client, registered_user):
    # Спроба входу з неправильним паролем
    bad_login = client.post(
        "/login",
        data={
            "email": registered_user["email"],
            "password": "wrongpassword",
        },
        follow_redirects=True,
    )
    assert bad_login.status_code == 200
    assert b"Login unsuccessful" in bad_login.data

    # Успішний вхід
    login_resp = client.post(
        "/login",
        data={
            "email": registered_user["email"],
            "password": registered_user["password"],
            "remember": True,
        },
        follow_redirects=True,
    )
    assert login_resp.status_code == 200
    assert b"Welcome, oscar!" in login_resp.data
    assert b"oscar@gmail.com" in login_resp.data

    # Перевірка доступу до сторінки всіх користувачів
    users_resp = client.get("/users")
    assert users_resp.status_code == 200
    assert b"Users List (1)" in users_resp.data
    assert b"oscar@gmail.com" in users_resp.data

    # Авторизований користувач при заході на /login перенаправляється на /account
    redir_login = client.get("/login", follow_redirects=False)
    assert redir_login.status_code == 302
    assert "/account" in redir_login.headers["Location"]

    # Вихід із системи
    logout_resp = client.get("/logout", follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b"You have been logged out." in logout_resp.data

    # Після виходу доступ до /account знову закритий
    after_logout = client.get("/account", follow_redirects=False)
    assert after_logout.status_code == 302
    assert "/login" in after_logout.headers["Location"]
