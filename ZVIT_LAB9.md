# Лабораторна робота № 9. Побудова системи реєстрації та входу користувачів. Модуль Flask-Login

## Мета роботи
* Навчитися використовувати розширення `Flask-Bcrypt` для безпечного хешування та перевірки паролів користувачів.
* Реалізувати форми реєстрації (`RegistrationForm`) та входу (`LoginForm`) із валідацією полів та перевіркою унікальності даних у базі даних.
* Налаштувати автентифікацію користувачів, управління сесіями та захист маршрутів за допомогою `Flask-Login` (`UserMixin`, `@login_manager.user_loader`, `login_user`, `logout_user`, `@login_required`, `current_user`).
* Написати автоматизовані модульні та функціональні тести (`pytest`) для перевірки сторінок, реєстрації, входу та виходу.

---

## Хід виконання роботи

### Частина 1. Реєстрація користувачів та хешування паролів (`Flask-Bcrypt`)

1. **Підключення `Flask-Bcrypt` (`app/__init__.py`):**
   Встановлено бібліотеку `flask-bcrypt`, ініціалізовано екземпляр `bcrypt = Bcrypt()` та зареєстровано у фабриці застосунку `bcrypt.init_app(app)`.
2. **Тестування хешування у `flask shell` (Пункт 2):**
   У терміналі `flask --app run shell` створено користувача з паролем, захешованим методом `bcrypt.generate_password_hash('secret').decode('utf-8')`, збережено у БД та перевірено рівність через `bcrypt.check_password_hash(user.password, 'secret')` (результат — `True`).
3. **Сторінка реєстрації (`/register`):**
   * У `app/forms.py` створено `RegistrationForm` із валідаторами `DataRequired()`, `Length()`, `Regexp()` (для `username`), `Email()` та `EqualTo('password')`.
   * Реалізовано методи `validate_username` і `validate_email`, які перевіряють наявність дублікатів у базі даних.
   * У маршруті `/register` (`app/user_routes.py`) пароль перед збереженням хешується через `User.hash_password(form.password.data)`.
4. **Сторінка входу (`/login`) та профілю (`/account`):**
   * У моделі `User` додано методи `hash_password` і `check_password`.
   * Створено `LoginForm` (поля `email`, `password`, `remember`) та шаблон `login.html`.
   * Реалізовано маршрут `/account` та шаблон `account.html` із виведенням імені та електронної пошти поточного користувача.
5. **Список зареєстрованих користувачів (`/users`):**
   * Реалізовано сторінку `users.html`, яка виводить загальну кількість користувачів (`Users List ({{ users|length }})`) та таблицю з полями `Id`, `Username`, `Email`.

---

### Частина 2. Авторизація та захист сторінок (`Flask-Login`)

1. **Налаштування `LoginManager` (`app/__init__.py`):**
   Ініціалізовано `login_manager = LoginManager()`, задано `login_manager.login_view = "user.login"`, `login_manager.login_message = "Please log in to access this page."` та `login_manager.login_message_category = "warning"`.
2. **Модель `User` та `user_loader` (`app/models.py`):**
   * Клас `User` наслідує `UserMixin`.
   * Додано завантажувач `@login_manager.user_loader def load_user(user_id): return db.session.get(User, int(user_id))`.
3. **Захист маршрутів та динамічне меню (`app/user_routes.py`, `app/templates/base.html`):**
   * Сторінки `/account`, `/users` та `/logout` захищено декоратором `@login_required`.
   * При переході авторизованого користувача (`current_user.is_authenticated`) на `/login` або `/register` відбувається автоматичне перенаправлення на `/account`.
   * У `base.html` навігаційне меню змінюється залежно від стану автентифікації: для гостей відображаються `Login` та `Register`, а для авторизованих — `Users`, `Account` та `Logout`.

---

### Частина 3. Автоматизоване тестування (`pytest`)

У каталозі `tests/` (`conftest.py`, `test_auth.py`) реалізовано набір тестів із використанням ізольованої тестової БД SQLite у пам'яті (`TestConfig`):
* `test_register_page_loads`, `test_login_page_loads` — перевірка HTTP-статусу `200` та коректного рендерингу шаблонів реєстрації й входу.
* `test_user_registration_saves_hashed_password` — перевірка створення запису в БД, формату bcrypt-хешу (`$2b$...`) та валідації пароля.
* `test_duplicate_email_registration_fails` — перевірка блокування повторної реєстрації з тим самим `email`.
* `test_protected_routes_redirect_anonymous_user` — перевірка перенаправлення анонімного користувача зі сторінок `/account` та `/users` на `/login`.
* `test_login_and_logout_flow` — перевірка входу з невірним і вірним паролями, доступу до `/account` і `/users`, редіректу авторизованого користувача зі сторінки `/login` та завершення сесії через `/logout`.

Запуск тестів:
```bash
pytest -v
```
