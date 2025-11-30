import os

from app import create_app, db
from app.services.posts import ensure_flair_column

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        ensure_flair_column()
    app.run(
        debug=True,
        host=os.environ.get("FLASK_RUN_HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", 5000)),
    )
