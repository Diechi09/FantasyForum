import json
from datetime import datetime

from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from forms import CommentForm, LoginForm, PostForm, RegistrationForm

from .models import Post
from .services.auth import authenticate_user, create_user, find_existing_user
from .services.posts import (
    FLAIRS,
    add_comment as add_comment_service,
    comments_payload,
    create_post,
    delete_post as delete_post_service,
    export_posts_data,
    list_posts,
    paginate_posts,
    post_to_dict,
    stats_payload,
    update_post,
)


def register_routes(app):
    @app.route("/")
    @app.route("/home")
    def home():
        selected_flair = request.args.get("flair")
        posts = list_posts(selected_flair)
        return render_template(
            "home.html", title="Home", posts=posts, flairs=FLAIRS, selected_flair=selected_flair
        )

    @app.route("/about")
    def about():
        return render_template("about.html", title="About")

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        form = RegistrationForm()
        if form.validate_on_submit():
            exists = find_existing_user(form.username.data, form.email.data)
            if exists:
                flash("Username or email already taken.", "danger")
                return redirect(url_for("register"))
            user = create_user(form.username.data, form.email.data, form.password.data)
            login_user(user)
            flash(f"Welcome, {user.username}! Your account is ready.", "success")
            return redirect(url_for("home"))
        return render_template("register.html", title="Register", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        form = LoginForm()
        if form.validate_on_submit():
            user = authenticate_user(form.email.data, form.password.data)
            if user:
                login_user(user, remember=form.remember.data)
                flash(f"Welcome back, {user.username}!", "success")
                next_page = request.args.get("next")
                return redirect(next_page or url_for("home"))
            flash("Login unsuccessful. Check email and password.", "danger")
        return render_template("login.html", title="Login", form=form)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logged out.", "success")
        return redirect(url_for("home"))

    @app.route("/post/new", methods=["GET", "POST"])
    @login_required
    def new_post():
        form = PostForm()
        if form.validate_on_submit():
            create_post(
                title=form.title.data,
                flair=form.flair.data,
                content=form.content.data,
                author=current_user,
            )
            flash("Post published!", "success")
            return redirect(url_for("home"))
        return render_template("post_create.html", title="New Post", form=form)

    @app.route("/post/<int:post_id>")
    def post_detail(post_id):
        post = Post.query.get_or_404(post_id)
        return render_template("post_detail.html", title=post.title, post=post)

    @app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_post(post_id):
        post = Post.query.get_or_404(post_id)
        if post.author != current_user:
            abort(403)
        form = PostForm()
        if form.validate_on_submit():
            update_post(post, form.title.data, form.flair.data, form.content.data)
            flash("Post updated.", "success")
            return redirect(url_for("post_detail", post_id=post.id))
        elif request.method == "GET":
            form.title.data = post.title
            form.flair.data = post.flair
            form.content.data = post.content
        return render_template("post_edit.html", title="Edit Post", form=form, post=post)

    @app.route("/post/<int:post_id>/delete", methods=["POST"])
    @login_required
    def delete_post(post_id):
        post = Post.query.get_or_404(post_id)
        if post.author != current_user:
            abort(403)
        delete_post_service(post)
        flash("Post deleted.", "success")
        return redirect(url_for("home"))

    @app.route("/post/<int:post_id>/comment", methods=["POST"])
    @login_required
    def add_comment(post_id):
        post = Post.query.get_or_404(post_id)
        form = CommentForm()
        if form.validate_on_submit():
            add_comment_service(post, current_user, form.content.data)
            flash("Comment added.", "success")
        else:
            flash("Could not add comment.", "danger")
        return redirect(url_for("post_detail", post_id=post.id))

    @app.get("/api/health")
    def api_health():
        return jsonify({"status": "ok"}), 200

    @app.get("/api/posts")
    def api_posts():
        flair = request.args.get("flair")
        q_text = request.args.get("q", "")
        try:
            page = max(int(request.args.get("page", 1)), 1)
        except ValueError:
            page = 1
        try:
            per_page = min(max(int(request.args.get("per_page", 10)), 1), 50)
        except ValueError:
            per_page = 10

        pagination = paginate_posts(flair, q_text, page, per_page)
        items = [post_to_dict(p) for p in pagination.items]

        return (
            jsonify(
                {
                    "items": items,
                    "page": pagination.page,
                    "per_page": per_page,
                    "pages": pagination.pages,
                    "total": pagination.total,
                    "flair": flair,
                    "q": q_text,
                }
            ),
            200,
        )

    @app.get("/api/posts/<int:post_id>")
    def api_post_detail(post_id):
        post = Post.query.get_or_404(post_id)
        return jsonify(post_to_dict(post, with_content=True)), 200

    @app.get("/api/posts/<int:post_id>/comments")
    def api_post_comments(post_id):
        post = Post.query.get_or_404(post_id)
        return jsonify(comments_payload(post)), 200

    @app.get("/api/stats")
    def api_stats():
        return jsonify(stats_payload()), 200

    @app.get("/api/export/posts")
    def api_export_posts():
        data = export_posts_data()
        filename = f'posts-export-{datetime.utcnow().strftime("%Y%m%d-%H%M%SZ")}.json'
        return app.response_class(
            response=json.dumps(data, ensure_ascii=False, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.route("/api-demo")
    def api_demo():
        return render_template("api_demo.html", title="API Demo")
