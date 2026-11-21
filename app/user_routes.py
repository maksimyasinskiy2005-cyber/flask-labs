from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import select
from app import db
from app.models import User
from app.forms import RegistrationForm, LoginForm

user_bp = Blueprint("user", __name__)


@user_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("user.account"))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = User.hash_password(form.password.data)
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
        )
        db.session.add(new_user)
        db.session.commit()

        flash(f"Account created for {form.username.data}!", "success")
        return redirect(url_for("user.login"))

    return render_template("register.html", form=form, title="Register")


@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("user.account"))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(select(User).where(User.email == form.email.data))
        if user and user.check_password(form.password.data):
            session["username"] = user.username
            login_user(user, remember=form.remember.data)
            flash("You have been logged in!", "success")
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("user.account"))

        flash("Login unsuccessful. Please check email and password.", "danger")

    return render_template("login.html", form=form, title="Login")


@user_bp.route("/account")
@login_required
def account():
    return render_template("account.html", user=current_user, title="Account")


@user_bp.route("/users")
@login_required
def users_list():
    users = db.session.scalars(select(User).order_by(User.id)).all()
    return render_template("users.html", users=users, title="Users List")


@user_bp.route("/logout")
@login_required
def logout():
    session.pop("username", None)
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("user.login"))
