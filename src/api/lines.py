from fastapi import APIRouter, HTTPException
from enum import Enum
from src import database as db
from fastapi.params import Query

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

    line = db.lines.get(line_id)
    if line:
        character = db.characters.get(line.c_id)
        movie = db.movies.get(line.movie_id)

        result = {
            "line_id": line_id,
            "character_id": line.c_id,
            "character": character and character.name,
            "movie_id": line.movie_id,
            "movie": movie and movie.title,
            "text": line.line_text,
        }
        return result

    raise HTTPException(status_code=404, detail="line not found.")



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
    
    if text or movie_title:
        def filter_fn(l):
            return (text in l.line_text) and (movie_title in db.movies.get(l.movie_id).title)
            
    else:
            def filter_fn(l):
                return True
    
    if sort == line_sort_options.movie_title:
            def sort_fn(l):
                return db.movies.get(l.movie_id).title
            
    elif sort == line_sort_options.character:
            def sort_fn(l):
                return db.characters.get(l.c_id).name
    
    lines = sorted(
            (l for l in db.lines.values() if filter_fn(l)),
            key=sort_fn,
        )
    
    json = (

                {
                    "line_id": line.id,
                    "character": db.characters[line.c_id].name,
                    "movie": db.movies[line.movie_id].title,
                    "text": line.line_text,
                }
                for line in lines[offset:offset + limit]

    )
    return json

@router.get("/conversations/{conv_id}", tags=["conversations"])
def get_conversation(conv_id: int):
    """
    This endpoint returns a single conversation by its identifier. For each conversation it returns:
    * `conv_id`: the internal id of the conversation.
    * `character`: The name of the character that said the line.
    * `movie`: The title of the movie the line is from.
    * `comversation`: The text of the conversation, including all lines that have the same conv_id.
    """

    conv = db.conversations.get(conv_id)
    if conv:
        movie = db.movies.get(conv.movie_id)
        result = {
            "conv_id": conv_id,
            "movie": movie and movie.title,
            "conversation": (
             {"character": db.characters.get(line.c_id).name,"line": line.line_text} for line in db.lines.values() if line.conv_id == conv_id
             )
            
        }
        return result
    raise HTTPException(status_code=404, detail="conversation not found.")


