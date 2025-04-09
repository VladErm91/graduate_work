import pytest
from fastapi.testclient import TestClient
from mongo_app.app.main import app

client = TestClient(app)


@pytest.fixture
def test_user():
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword",
    }


@pytest.fixture
def test_movie():
    return {"title": "Test Movie", "description": "This is a test movie."}


@pytest.fixture
def test_like(test_user, test_movie):
    return {"user_id": test_user["_id"], "movie_id": test_movie["_id"], "rating": 8}


@pytest.fixture
def test_review(test_user, test_movie):
    return {
        "user_id": test_user["_id"],
        "movie_id": test_movie["_id"],
        "content": "This is a test review.",
        "publication_date": "2023-10-01T00:00:00Z",
        "additional_data": {"key": "value"},
        "likes": 5,
        "dislikes": 2,
    }


@pytest.fixture
def test_bookmark(test_user, test_movie):
    return {"user_id": test_user["_id"], "movie_id": test_movie["_id"]}


def test_create_user(test_user):
    response = client.post("/users/", json=test_user)
    assert response.status_code == 200
    assert response.json()["username"] == test_user["username"]


def test_create_movie(test_movie):
    response = client.post("/movies/", json=test_movie)
    assert response.status_code == 200
    assert response.json()["title"] == test_movie["title"]


def test_create_like(test_like):
    response = client.post("/likes/", json=test_like)
    assert response.status_code == 200
    assert response.json()["rating"] == test_like["rating"]


def test_create_review(test_review):
    response = client.post("/reviews/", json=test_review)
    assert response.status_code == 200
    assert response.json()["content"] == test_review["content"]


def test_create_bookmark(test_bookmark):
    response = client.post("/bookmarks/", json=test_bookmark)
    assert response.status_code == 200
    assert response.json()["user_id"] == test_bookmark["user_id"]


def test_delete_like(test_like):
    response = client.post("/likes/", json=test_like)
    like_id = response.json()["_id"]
    response = client.delete(f"/likes/{like_id}/")
    assert response.status_code == 200


def test_delete_review(test_review):
    response = client.post("/reviews/", json=test_review)
    review_id = response.json()["_id"]
    response = client.delete(f"/reviews/{review_id}/")
    assert response.status_code == 200


def test_delete_bookmark(test_bookmark):
    response = client.post("/bookmarks/", json=test_bookmark)
    bookmark_id = response.json()["_id"]
    response = client.delete(f"/bookmarks/{bookmark_id}/")
    assert response.status_code == 200
