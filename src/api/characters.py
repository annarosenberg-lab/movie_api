from fastapi import APIRouter, HTTPException
from enum import Enum
from collections import Counter
import sqlalchemy
from sqlalchemy import desc, func, select

from src import database as db
from fastapi.params import Query


router = APIRouter()


def get_num_lines_convo(character1_id, character2_id):
    "returns the number of lines between the same two characters"
    stmt = sqlalchemy.select(
        sqlalchemy.func.count(db.conversations.c.conversation_id)
    ).where(
         sqlalchemy.or_((db.conversations.c.character1_id == character1_id and db.conversations.c.character2_id == character2_id),
        (db.conversations.c.character1_id == character2_id and db.conversations.c.character2_id == character1_id))
    )
    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        return result.scalar()
    
def get_num_lines_character(character_id:int):
    "returns the number of lines a character has"
    stmt = sqlalchemy.select(
        sqlalchemy.func.count(db.lines.c.line_id)
    ).where(
        db.lines.c.character_id == character_id
    )
    with db.engine.connect() as conn:
        result = conn.execute(stmt)
        return result.scalar()
   

def get_top_convos(id: int):
    """
    c_id = character.id
    movie_id = character.movie_id
    all_convs = filter(
        lambda conv: conv.movie_id == movie_id
        and (conv.c1_id == c_id or conv.c2_id == c_id),
        db.conversations.values(),
    )
    line_counts = Counter()

    for conv in all_convs:
        other_id = conv.c2_id if conv.c1_id == c_id else conv.c1_id
        line_counts[other_id] += conv.num_lines

    return line_counts.most_common()
 """
    stmt = (
        sqlalchemy.select(
            db.conversations.c.character1_id,
            db.conversations.c.character2_id,
            db.conversations.c.movie_id,
        )
        .where(
            sqlalchemy.or_(
                db.conversations.c.character1_id == id, db.conversations.c.character2_id == id
            )
        )
    )

    with db.engine.connect() as conn:
        result = conn.execute(stmt).fetchall()
        line_counts = Counter()

        for conv in result:
            other_id = conv.character2_id if conv.character1_id == id else conv.character1_id
            line_counts[other_id] += get_num_lines_convo(id, other_id)

        return line_counts.most_common()


        """
            top_conversations": (
                {
                    "character_id": other_id,
                    "character": db.characters.other_id.name,
                    "gender": db.characters.other_id.gender,
                    "number_of_lines_together": lines,
                }
                for other_id, lines in get_top_convos(id)
            ),
            """


@router.get("/characters/{id}", tags=["characters"])
def get_character(id: int):
    """
    This endpoint returns a single character by its identifier. For each character
    it returns:
    * `character_id`: the internal id of the character. Can be used to query the
      `/characters/{character_id}` endpoint.
    * `character`: The name of the character.
    * `movie`: The movie the character is from.
    * `gender`: The gender of the character.
    * `top_conversations`: A list of characters that the character has the most
      conversations with. The characters are listed in order of the number of
      lines together. These conversations are described below.

    Each conversation is represented by a dictionary with the following keys:
    * `character_id`: the internal id of the character.
    * `character`: The name of the character.
    * `gender`: The gender of the character.
    * `number_of_lines_together`: The number of lines the character has with the
      originally queried character.
    """
    top_convos = get_top_convos(id)


    stmt = (
        sqlalchemy.select(
            db.characters.c.character_id, 
            db.characters.c.name, 
            db.movies.c.title,
            db.characters.c.gender
        ).select_from(
            sqlalchemy.join(db.characters, db.movies, db.characters.c.movie_id == db.movies.c.movie_id)
        ).where(
            db.characters.c.character_id == id
        )
    )

    with db.engine.connect() as conn:
        result = conn.execute(stmt).fetchone()
        json = {
            "character_id": result.character_id,
            "character": result.name,
            "movie": result.title,
            "gender": result.gender,
            "top_conversations": (
                {
                    "character_id": other_id,
                    "character": "TODO",
                    "gender": "TODO",
                    "number_of_lines_together": lines,
                }
                for other_id, lines in top_convos
            ),


         

        }

    return json
            

class character_sort_options(str, Enum):
    character = "character"
    movie = "movie"
    number_of_lines = "number_of_lines"


@router.get("/characters/", tags=["characters"])
def list_characters(
    name: str = "",
    limit: int = Query(50, ge=1, le=250),
    offset: int = Query(0, ge=0),
    sort: character_sort_options = character_sort_options.character,
):
    """
    This endpoint returns a list of characters. For each character it returns:
    * `character_id`: the internal id of the character. Can be used to query the
      `/characters/{character_id}` endpoint.
    * `character`: The name of the character.
    * `movie`: The movie the character is from.
    * `number_of_lines`: The number of lines the character has in the movie.

    You can filter for characters whose name contains a string by using the
    `name` query parameter.

    You can also sort the results by using the `sort` query parameter:
    * `character` - Sort by character name alphabetically.
    * `movie` - Sort by movie title alphabetically.
    * `number_of_lines` - Sort by number of lines, highest to lowest.

    The `limit` and `offset` query
    parameters are used for pagination. The `limit` query parameter specifies the
    maximum number of results to return. The `offset` query parameter specifies the
    number of results to skip before returning results.
    """
    if sort == character_sort_options.character:
        sort_by = db.characters.c.name
    elif sort == character_sort_options.movie:
        sort_by = db.movies.c.title
    elif sort == character_sort_options.number_of_lines:
        sort_by = sqlalchemy.desc("number_of_lines")
    
    else:
        raise HTTPException(status_code=400, detail="Invalid sort option")
    stmt = (
          
          sqlalchemy.select(
              db.characters.c.character_id,
              db.characters.c.name,
              db.movies.c.title,  
              sqlalchemy.func.count(db.lines.c.line_id).label("number_of_lines")
              )
          .select_from(
            sqlalchemy.join(db.characters,db.movies, db.movies.c.movie_id == db.characters.c.movie_id))
            .join(db.lines, db.characters.c.character_id == db.lines.c.character_id)
            .group_by(
              db.characters.c.character_id,
              db.movies.c.title, 
          )
          .order_by(sort_by)
          .limit(limit)
          .offset(offset)

      )

    if name != "":
        stmt = stmt.where(db.characters.c.name.ilike(f"%{name}%"))


    with db.engine.connect() as conn:
        result = conn.execute(stmt).fetchall()
        return [
            {
                "character_id": row.character_id,
                "character": row.name,
                "movie": row.title,
                "number_of_lines": get_num_lines_character(row.character_id),
            }
            for row in result
        ]


