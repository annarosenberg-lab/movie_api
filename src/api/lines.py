from fastapi import APIRouter, HTTPException
from enum import Enum
from src import database as db
from fastapi.params import Query
from collections import Counter
import sqlalchemy
from sqlalchemy import desc, func, select


router = APIRouter()

@router.get("/lines/{line_id}", tags=["lines"])
def get_line(line_id: int):
    """
    This endpoint returns a single line by its identifier. For each line it returns:
    * `line_id`: the internal id of the line.
    * `character_id`: the internal id of the character that said the line.
    * `character`: The name of the character that said the line.
    * `movie_id`: the internal id of the movie the line is from.
    * `movie`: The title of the movie the line is from.
    * `text`: The text of the line.
    """
    stmt = sqlalchemy.select(
        db.lines.c.line_id,
        db.lines.c.character_id,
        db.characters.c.name.label("character"),
        db.lines.c.movie_id,
        db.movies.c.title.label("movie"),
        db.lines.c.line_text.label("text"),
    ).select_from(
        db.lines.join(
            db.characters, db.lines.c.character_id == db.characters.c.character_id
        ).join(
            db.movies, db.lines.c.movie_id == db.movies.c.movie_id
        )
    ).where(db.lines.c.line_id == line_id)

    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Line not found")
        json = {}
        for row in result:
            json["line_id"] = row.line_id
            json["character_id"] = row.character_id
            json["character"] = row.character
            json["movie_id"] = row.movie_id
            json["movie"] = row.movie
            json["text"] = row.text
        return json




class line_sort_options(str, Enum):
    movie_title = "movie_title"
    character = "character"


@router.get("/lines/", tags=["lines"])
def list_lines(text: str = "",
    movie_title: str = "",
    limit: int = Query(50, ge=1, le=250),
    offset: int = Query(0, ge=0),
    sort: line_sort_options = line_sort_options.movie_title
):
    """
    This endpoint returns a list of lines. For each line it returns:
    * `line_id`: the internal id of the line.
    * `character`: The name of the character that said the line.
    * `movie`: The title of the movie the line is from.
    * `text`: The text of the line.

    You can filter lines by the text of the line using the `text` query parameter, additionally you can filter
    lines by the movie title with the `movie_title` query parameter.

    You can sort the lines by the movie title and character name by using the `sort` query parameter. 

    The `limit` and `offset` query
    parameters are used for pagination. The `limit` query parameter specifies the
    maximum number of results to return. The `offset` query parameter specifies the
    number of results to skip before returning results.
    """
    if sort == line_sort_options.movie_title:
        sort_by = db.movies.c.title
    elif sort == line_sort_options.character:
        sort_by = db.characters.c.name


    stmt = sqlalchemy.select(
        db.lines.c.line_id,
        db.characters.c.name.label("character"),
        db.movies.c.title.label("movie"),
        db.lines.c.line_text.label("text"),
    ).select_from(
        db.lines.join(
            db.characters, db.lines.c.character_id == db.characters.c.character_id
        ).join(
            db.movies, db.lines.c.movie_id == db.movies.c.movie_id
        )
    ).where(
        db.lines.c.line_text.like(f"%{text}%")
    ).where(
        db.movies.c.title.like(f"%{movie_title}%")
    ).order_by(
        sort_by
    ).limit(limit).offset(offset)

    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        json = []
        for row in result:
            json.append({
                "line_id": row.line_id,
                "character": row.character,
                "movie": row.movie,
                "text": row.text
            })
        return json


    


