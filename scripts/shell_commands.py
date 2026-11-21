"""
Команди для виконання у flask shell (Пункт 2 Лабораторної роботи №9).
Запуск: flask --app run shell
"""

def create_hashed_user():
    from sqlalchemy import select
    from app import db, bcrypt
    from app.models import User

    existing = db.session.scalar(select(User).where(User.username == "yulia12"))
    if existing:
        db.session.delete(existing)
        db.session.commit()

    user = User(username="yulia12", email="yulia12@gmail.com", password="secret")
    print("Пароль до хешування:", user.password)

    hashed = bcrypt.generate_password_hash("secret").decode("utf-8")
    user.password = hashed
    print("Хешований пароль:", user.password)

    db.session.add(user)
    db.session.commit()

    saved_user = db.session.scalar(select(User).where(User.username == "yulia12"))
    is_valid = bcrypt.check_password_hash(saved_user.password, "secret")
    print("Перевірка рівності по хешу (secret):", is_valid)
    is_wrong = bcrypt.check_password_hash(saved_user.password, "wrong_pass")
    print("Перевірка рівності по хешу (wrong_pass):", is_wrong)
