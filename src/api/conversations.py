from fastapi import APIRouter
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

    # TODO: Remove the following two lines. This is just a placeholder to show
    # how you could implement persistent storage.

        # Check that the characters are part of the movie
    db.execute(
        """
        SELECT * FROM characters
        WHERE movie_id = %s
        AND id IN (%s, %s)
        """,
        (movie_id, conversation.character_1_id, conversation.character_2_id),
    )
    if db.cursor.rowcount != 2:
        return {"error": "Characters are not part of the movie"}

    # Check that the characters are not the same
    if conversation.character_1_id == conversation.character_2_id:
        return {"error": "Characters cannot be the same"}

    # Check that the lines match the characters
    for line in conversation.lines:
        if line.character_id not in (conversation.character_1_id, conversation.character_2_id):
            return {"error": "Line does not match characters"}

    # Create the conversation
    db.execute(
        """
        INSERT INTO conversations (movie_id, character_1_id, character_2_id)
        VALUES (%s, %s, %s)
        """,
        (movie_id, conversation.character_1_id, conversation.character_2_id),
    )
    conversation_id = db.cursor.lastrowid

    # Create the lines
    for line in conversation.lines:
        db.execute(
            """
            INSERT INTO lines (conversation_id, character_id, line_text, sort)
            VALUES (%s, %s, %s, %s)
            """,
            (conversation_id, line.character_id, line.line_text, line.sort),
        )

    return {"conversation_id": conversation_id}
 

