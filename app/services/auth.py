from ..extensions import db
from ..models import User


def find_existing_user(username: str, email: str):
    return User.query.filter((User.username == username) | (User.email == email)).first()


def create_user(username: str, email: str, password: str) -> User:
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email: str, password: str):
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        return user
    return None
