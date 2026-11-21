from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from app import db
from app.models import Post, Tag
from app.forms import PostForm

post_bp = Blueprint("post", __name__)


@post_bp.route("/")
def index():
    stmt = (
        select(Post)
        .options(joinedload(Post.user), selectinload(Post.tags))
        .order_by(Post.id.desc())
    )
    posts = db.session.scalars(stmt).all()
    return render_template("index.html", posts=posts)


@post_bp.route("/add_post", methods=["GET", "POST"])
@login_required
def add_post():
    form = PostForm()
    if not form.is_submitted() and current_user.is_authenticated:
        form.author_id.data = current_user.id

    if form.validate_on_submit():
        selected_tags = []
        if form.tags.data:
            selected_tags = db.session.scalars(
                select(Tag).where(Tag.id.in_(form.tags.data))
            ).all()

        new_post = Post(
            title=form.title.data,
            content=form.content.data,
            is_active=form.is_active.data,
            publish_date=form.publish_date.data,
            category=form.category.data,
            user_id=form.author_id.data,
            tags=selected_tags,
        )
        db.session.add(new_post)
        db.session.commit()
        flash("Пост успішно створено!", "success")
        return redirect(url_for("post.post_detail", post_id=new_post.id))

    return render_template("add_post.html", form=form)


@post_bp.route("/post/<int:post_id>")
def post_detail(post_id: int):
    stmt = (
        select(Post)
        .options(joinedload(Post.user), selectinload(Post.tags))
        .where(Post.id == post_id)
    )
    post = db.session.scalar(stmt)
    if post is None:
        return "Пост не знайдено", 404
    return render_template("post_detail.html", post=post)
