from app.models import Post, User


def test_register_login_and_create_post(app, client):
    registration_payload = {
        "username": "integration-user",
        "email": "integration@example.com",
        "password": "strongpass",
        "confirm_password": "strongpass",
    }

    register_response = client.post("/register", data=registration_payload, follow_redirects=True)
    assert register_response.status_code == 200

    with app.app_context():
        created_user = User.query.filter_by(email="integration@example.com").first()
        assert created_user is not None

    post_payload = {
        "title": "Integration Adventure",
        "flair": "OTHER",
        "content": "Documenting an end-to-end journey.",
    }
    create_post_response = client.post("/post/new", data=post_payload, follow_redirects=True)
    assert create_post_response.status_code == 200

    with app.app_context():
        post = Post.query.filter_by(title="Integration Adventure").first()
        assert post is not None
        assert post.author.email == "integration@example.com"
        detail_response = client.get(f"/api/posts/{post.id}")
    assert detail_response.status_code == 200
    payload = detail_response.get_json()
    assert payload["title"] == "Integration Adventure"
    assert payload["content"] == "Documenting an end-to-end journey."


def test_comment_flow_through_routes(app, login, sample_post):
    comment_response = login.post(
        f"/post/{sample_post.id}/comment",
        data={"content": "First!"},
        follow_redirects=True,
    )
    assert comment_response.status_code == 200

    api_comments_response = login.get(f"/api/posts/{sample_post.id}/comments")
    assert api_comments_response.status_code == 200
    comments_payload = api_comments_response.get_json()
    assert isinstance(comments_payload, dict)
    assert comments_payload.get("total") == 1
    assert any(c.get("content") == "First!" for c in comments_payload.get("items", []))