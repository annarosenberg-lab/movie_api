from fastapi import APIRouter, HTTPException
from src import database as db
from pydantic import BaseModel
from typing import List
from datetime import datetime


# FastAPI is inferring what the request body should look like
# based on the following two classes.
class LinesJson(BaseModel):
    character_id: int
    line_text: str


class ConversationJson(BaseModel):
    character_1_id: int
    character_2_id: int
    lines: List[LinesJson]


router = APIRouter()


@router.post("/movies/{movie_id}/conversations/", tags=["movies"])
def add_conversation(movie_id: int, conversation: ConversationJson):
    """
    This endpoint adds a conversation to a movie. The conversation is represented
    by the two characters involved in the conversation and a series of lines between
    those characters in the movie.

    The endpoint ensures that all characters are part of the referenced movie,
    that the characters are not the same, and that the lines of a conversation
    match the characters involved in the conversation.

    Line sort is set based on the order in which the lines are provided in the
    request body.

    The endpoint returns the id of the resulting conversation that was created.
    """
    
    """
        Function limitations:
        - Does not check if the conversation is actually apart of the movie, 
        users have discretion to add whatever lines they want to whatever movie they want.
        - This function is difficult to test because the test functions with valid input modify
        the database each time they are called and the database is not reset after each test.
        - This function is slow and not very efficient, it iterates through the entire database to
        find the max id.
        - This function is not very secure, it does not check if the user is authorized
        to add a conversation/line.
        - This function is not very scalable, it does not check if the conversation/line
        already exists, and duplicate conversations/lines may be added to the database.
        - This would no function well in the case of multiple simultaneous requests, 
        the database could be modified in an unexpected way.
        - Race conditions may occur if multiple users are trying to add a conversation/line 
        at the same time.
    """

  
    try:
        movie = db.movies[movie_id]
        character_1 = db.characters[conversation.character_1_id]
        character_2 = db.characters[conversation.character_2_id]
    except KeyError:
        raise HTTPException(status_code=404, detail="movie or character not found.")
    
    if (character_1.movie_id != movie_id or character_2.movie_id != movie_id) or (character_1.id == character_2.id):
        raise HTTPException(status_code=404, detail="invalid characters.")
    
    for line in conversation.lines:
        if line.character_id != character_1.id and line.character_id != character_2.id:
            raise HTTPException(status_code=404, detail="invalid lines.")
        
    conversation_id = max(d.id for d in db.conversations.values()) + 1

    line_sort = 1
    line_id = max(d.id for d in db.lines.values()) + 1

    for line in conversation.lines:
        db.lines[line_id] = db.Line(line_id, line.character_id, movie_id, conversation_id, line_sort, line.line_text)
        db.convo_lines.append({"line_id": line_id, "character_id": line.character_id, "movie_id": movie_id, "conversation_id": conversation_id, "line_sort": line_sort, "line_text": line.line_text})
        db.upload_new_lines()
        line_sort += 1
        line_id += 1

    db.conversations[conversation_id] = db.Conversation(conversation_id, character_1.id, character_2.id, movie_id, len(conversation.lines))
    db.convos.append({"conversation_id": conversation_id, "character1_id": character_1.id, "character2_id": character_2.id, "movie_id": movie_id})
    db.upload_new_conversation()

    return {"conversation_id": conversation_id}

    
  



