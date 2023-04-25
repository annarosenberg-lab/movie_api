
from fastapi.testclient import TestClient

from src.api.server import app

import json

client = TestClient(app)

#Testing with characters not from referenced movie
def test_add_conversation_1():
    test = {
        "character_1_id": 78,
        "character_2_id": 79,
        "lines": [
            {
                "character_id": 78,
                "line_text": "test"
            }
        ]
    }
    response = client.post("/movies/0/conversations/", json=test)
    assert response.status_code == 404

#Testing with idenitcal characters 
def test_add_conversation_2():
    test = {
        "character_1_id": 0,
        "character_2_id": 0,
        "lines": [
            {
                "character_id": 0,
                "line_text": "test"
            }
        ]
    }
    response = client.post("/movies/0/conversations/", json=test)
    assert response.status_code == 404

#Testing with invalid character lines
def test_add_conversation_3():
    test = {
        "character_1_id": 0,
        "character_2_id": 2,
        "lines": [
            {
                "character_id": 1,
                "line_text": "test"
            }
        ]
    }
    response = client.post("/movies/0/conversations/", json=test)
    assert response.status_code == 404

#Testing with invalid movie
def test_add_conversation_4():
    test = {
        "character_1_id": 51,
        "character_2_id": 52,
        "lines": [
            {
                "character_id": 1,
                "line_text": "test"
            }
        ]
    }
    response = client.post("/movies/888888/conversations/", json=test)
    assert response.status_code == 404
    
    
#Testing with valid inputs    
def test_add_conversation_5():
    test = {
        "character_1_id": 0,
        "character_2_id": 1,
        "lines": [
            {
                "character_id": 1,
                "line_text": "test passed for test_add_conversation_5"
            }
        ]
    }
    response = client.post("/movies/0/conversations/", json=test)
    assert response.status_code == 200
