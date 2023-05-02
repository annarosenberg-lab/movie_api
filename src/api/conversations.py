from fastapi import APIRouter, HTTPException
from src import database as db
from pydantic import BaseModel
from typing import List
from datetime import datetime
from collections import Counter
import sqlalchemy
from sqlalchemy import desc, func, select


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

@router.get("/conversations/{conv_id}", tags=["conversations"])
def get_conversation(conv_id: int):
    """
    This endpoint returns a single conversation by its identifier. For each conversation it returns:
    * `conv_id`: the internal id of the conversation.
    * `character`: The name of the character that said the line.
    * `movie`: The title of the movie the line is from.
    * `comversation`: The text of the conversation, including all lines that have the same conv_id.
    """
    stmt = sqlalchemy.select(
        db.conversations.c.conversation_id,
        db.characters.c.name.label("character"),
        db.movies.c.title.label("movie"),
        db.lines.c.line_text.label("line"),

    ).select_from(
        db.conversations.join(
            db.movies, db.conversations.c.movie_id == db.movies.c.movie_id
        )
        .join(
            db.lines, db.conversations.c.conversation_id == db.lines.c.conversation_id
        )
    ).join(
            db.characters, db.lines.c.character_id == db.characters.c.character_id
        ).where(db.conversations.c.conversation_id == conv_id)

    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        convos = conn.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")

        convo = []
        for row in convos:
            line = {}
            line["character"] = row.character
            line["line"] = row.line
            convo.append(line)

        json= {}
        for row in result:
            json["conv_id"] = row.conversation_id
            json["movie"] = row.movie
            json["conversation"] = convo

    return json



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

    stmt = sqlalchemy.select(
        db.movies.c.movie_id,
        db.characters.c.name.label("character"),
    ).select_from(db.movies.join(db.characters, db.movies.c.movie_id == db.characters.c.movie_id)).where(db.movies.c.movie_id == movie_id and
            db.characters.c.character_id == conversation.character_1_id or
            db.characters.c.character_id == conversation.character_2_id)


    """

    #check if movie exists
    stmt = sqlalchemy.select(db.movies.c.movie_id).where(db.movies.c.movie_id == movie_id)
    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Movie not found")
    
    #check if characters are the same
    if conversation.character_1_id == conversation.character_2_id:
        raise HTTPException(status_code=404, detail="Characters cannot be the same")
    
    #check if characters exist in movie
    stmt = sqlalchemy.select(
        db.movies.c.movie_id,
        db.characters.c.name.label("character"),
    ).select_from(db.movies.join(db.characters, db.movies.c.movie_id == db.characters.c.movie_id)).where(db.movies.c.movie_id == movie_id and
            (db.characters.c.character_id == conversation.character_1_id or
            db.characters.c.character_id == conversation.character_2_id))
    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        if result.rowcount < 2:
            print(result.rowcount == 2)
            raise HTTPException(status_code=404, detail="Characters not found in movie")
        
    #check if lines match characters
    for line in conversation.lines:
        if line.character_id != conversation.character_1_id and line.character_id != conversation.character_2_id:
            raise HTTPException(status_code=404, detail="Character does not match line")

    #get the next conversation id and line id
    with db.engine.connect() as conn:
        convo_num_ids = conn.execute(sqlalchemy.select(func.max(db.conversations.c.conversation_id)))
        line_num_ids = conn.execute(sqlalchemy.select(func.max(db.lines.c.line_id)))
        for row in convo_num_ids:
            conversation_id = row[0] + 1
        for row in line_num_ids:
            line_id = row[0] + 1
        
    #upload new conversation 
    with db.engine.begin() as conn:
        conn.execute(
            sqlalchemy.insert(db.conversations),
            [
                {"conversation_id": conversation_id,
                "character1_id": conversation.character_1_id,
                "character2_id": conversation.character_2_id,
                "movie_id": movie_id,},
            ],
        
     )
        
    #upload new lines
    line_sort = 1
    for line in conversation.lines:
        with db.engine.begin() as conn:
            conn.execute(
                sqlalchemy.insert(db.lines),
                [
                    {"line_id": line_id,
                    "character_id": line.character_id,
                    "movie_id": movie_id,
                    "conversation_id": conversation_id,
                    "line_sort": line_sort,
                    "line_text": line.line_text,
                    },
                ])
        line_sort += 1
        line_id += 1
        
    return {"conversation_id": conversation_id}



  
    
    

    
  





    
  



