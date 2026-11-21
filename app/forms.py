from datetime import datetime as dt
from flask_wtf import FlaskForm
from sqlalchemy import select
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    BooleanField,
    DateTimeLocalField,
    SelectField,
    SelectMultipleField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    ValidationError,
    Regexp,
)
from app import db
from app.models import User, Tag

CATEGORIES = [
    ("Tech", "Tech"),
    ("Art", "Art"),
    ("Science", "Science"),
    ("LifeStyle", "LifeStyle"),
]


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=4, max=16),
            Regexp(
                r"^[A-Za-z][A-Za-z0-9_.]*$",
                message="Username must have only letters, numbers, dots or underscores",
            ),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=6),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Паролі повинні співпадати"),
        ],
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = db.session.scalar(select(User).where(User.username == username.data))
        if user:
            raise ValidationError(
                f"Користувач з таким іменем {username.data} вже існує"
            )

    def validate_email(self, email):
        user = db.session.scalar(select(User).where(User.email == email.data))
        if user:
            raise ValidationError(
                f"Користувач з таким емейлом {email.data} вже існує"
            )


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(min=2)])
    content = TextAreaField(
        "Content",
        render_kw={"rows": 5, "cols": 40},
        validators=[DataRequired()],
    )
    is_active = BooleanField("Is this post active?", default=True)
    publish_date = DateTimeLocalField(
        "Publish Date",
        format="%Y-%m-%dT%H:%M",
        default=dt.now,
    )
    category = SelectField("Category", choices=CATEGORIES, validators=[DataRequired()])
    author_id = SelectField("Author", coerce=int, validators=[DataRequired()])
    tags = SelectMultipleField("Tags", coerce=int)
    submit = SubmitField("Add Post")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.author_id.choices = [
            (u.id, u.username)
            for u in db.session.scalars(select(User).order_by(User.id)).all()
        ]
        self.tags.choices = [
            (t.id, t.name)
            for t in db.session.scalars(select(Tag).order_by(Tag.name)).all()
        ]
