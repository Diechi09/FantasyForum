from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import text

from ..extensions import db
from ..models import Comment, Post

FLAIRS: List[Tuple[str, str]] = [
    ("TRADE_HELP", "TRADE HELP"),
    ("WAIVER_WIRE", "WAIVER WIRE ADVICE"),
    ("INJURY_TALK", "INJURY TALK"),
    ("OTHER", "OTHER"),
]


def ensure_flair_column():
    rows = db.session.execute(text("PRAGMA table_info(post)")).fetchall()
    cols = {row[1] for row in rows}
    if "flair" not in cols:
        db.session.execute(
            text("ALTER TABLE post ADD COLUMN flair VARCHAR(20) NOT NULL DEFAULT 'OTHER'")
        )
        db.session.commit()


def list_posts(selected_flair: Optional[str] = None):
    query = Post.query
    if selected_flair:
        query = query.filter_by(flair=selected_flair)
    return query.order_by(Post.date_posted.desc()).all()


def create_post(title: str, flair: str, content: str, author) -> Post:
    post = Post(title=title, flair=flair, content=content, author=author)
    db.session.add(post)
    db.session.commit()
    return post


def update_post(post: Post, title: str, flair: str, content: str) -> Post:
    post.title = title
    post.flair = flair
    post.content = content
    db.session.commit()
    return post


def delete_post(post: Post) -> None:
    db.session.delete(post)
    db.session.commit()


def post_to_dict(post: Post, with_content: bool = False):
    base = {
        "id": post.id,
        "title": post.title,
        "flair": post.flair,
        "author": post.author.username,
        "user_id": post.user_id,
        "date_posted": post.date_posted.isoformat(),
        "comments_count": len(post.comments),
    }
    if with_content:
        base["content"] = post.content
    return base


def paginate_posts(flair: Optional[str], q_text: str, page: int, per_page: int):
    query = Post.query
    if flair:
        query = query.filter_by(flair=flair)
    if q_text:
        like = f"%{q_text}%"
        query = query.filter((Post.title.ilike(like)) | (Post.content.ilike(like)))
    return query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=per_page)


def comments_payload(post: Post):
    data = [
        {
            "id": c.id,
            "post_id": post.id,
            "author": c.author.username,
            "user_id": c.user_id,
            "content": c.content,
            "date_posted": c.date_posted.isoformat(),
        }
        for c in sorted(post.comments, key=lambda x: x.date_posted)
    ]
    return {"items": data, "total": len(data)}


def stats_payload():
    counts = {
        "TRADE_HELP": Post.query.filter_by(flair="TRADE_HELP").count(),
        "WAIVER_WIRE": Post.query.filter_by(flair="WAIVER_WIRE").count(),
        "INJURY_TALK": Post.query.filter_by(flair="INJURY_TALK").count(),
        "OTHER": Post.query.filter_by(flair="OTHER").count(),
        "TOTAL": Post.query.count(),
    }
    latest = Post.query.order_by(Post.date_posted.desc()).limit(5).all()
    latest_items = [
        {
            "id": p.id,
            "title": p.title,
            "flair": p.flair,
            "author": p.author.username,
            "date_posted": p.date_posted.isoformat(),
        }
        for p in latest
    ]
    return {"counts": counts, "latest": latest_items}


def export_posts_data():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return [post_to_dict(post, with_content=True) for post in posts]


def add_comment(post: Post, author, content: str) -> Comment:
    comment = Comment(content=content, author=author, post=post)
    db.session.add(comment)
    db.session.commit()
    return comment
