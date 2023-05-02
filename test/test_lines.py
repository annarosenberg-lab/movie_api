from fastapi.testclient import TestClient

from src.api.server import app

import json

client = TestClient(app)


def test_get_line():
    response = client.get("/lines/66")
    assert response.status_code == 200

    with open("test/lines/66.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)



def test_404():
    response = client.get("/lines/400")
    assert response.status_code == 404


def test_sort_filter():
    response = client.get(
        "/lines/?text=Why&movie_title=10&limit=50&offset=0&sort=character"
    )
    assert response.status_code == 200

    with open(
        "test/lines/filter.json",
        encoding="utf-8",
    ) as f:
        assert response.json() == json.load(f)

def test_get_conversation():
    response = client.get("/conversations/0")
    assert response.status_code == 200

    with open("test/lines/0.json", encoding="utf-8") as f:
        assert response.json() == json.load(f)
