from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from capstone.database import db_dependency
from capstone.movie.schema import CreateMovie
from capstone.user.schema  import Login
from capstone.user.models import User
from capstone.movie.models import Movie as Movie_model
from capstone.auth.oauth2 import get_current_user
from capstone.movie.models import Rating as RatingModel
from capstone.movie.schema import Rating as RatingSchema
from capstone.movie.schema import Comment as CommentSchema
from capstone.movie.models import Comment as CommentModel
from capstone.movie.schema import ReplyComment

from capstone.logger import get_logger




logger = get_logger(__name__)


def create_movie(db : db_dependency, payload : CreateMovie, current_user : Login = Depends(get_current_user)):
    logger.info(f"User {current_user.username} is attempting to list a new movie: {payload.title}")
    user = db.query(User).filter(User.username == current_user.username).first()

    new_movie = Movie_model(
    title=payload.title,
    description=payload.description,
    release_date=datetime.now(timezone.utc),  # Set the release date to the current time in UTC
    updated_at=datetime.now(timezone.utc),    # Set the updated_at field to the current time in UTC
    user_id=user.id # Associate the movie with the user who created it
    )
    db.add(new_movie)  # Add the new movie instance to the database session
    db.commit()  # Commit the session to save the movie in the database
    db.refresh(new_movie)  # Refresh the instance with the latest data from the database
    logger.info(f"Movie '{new_movie.title}' has been listed by user {current_user.username} with ID {new_movie.id}.")
    return new_movie


def fetch_movies(db : db_dependency, offset : int = 0, limit : int =10):
    logger.info(f"Fetching movies with offset={offset} and limit={limit}")

    movies = db.query(Movie_model).offset(offset).limit(limit).all()
    logger.info(f"Fetched {len(movies)} movies with offset={offset} and limit={limit}")
    return movies

def fetch_movie_by_id(db : db_dependency, movie_id : int):
    logger.info(f"Fetching movie with ID={movie_id}")
    movie = db.query(Movie_model).filter(Movie_model.id == movie_id).first()

    if movie is None:
        logger.warning(f"Movie with ID={movie_id} not found")
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Movie not found"
        )
    logger.info(f"Movie with ID={movie_id} found: {movie.title}")

    return movie


def update_movie(db : db_dependency, movie_id : int, payload : CreateMovie, current_user : Login = Depends(get_current_user)):
    logger.info(f"User '{current_user.username}' is attempting to update movie with ID={movie_id}")
    user = db.query(User).filter(User.username == current_user.username).first()
            # Query the database for a movie with the given movie ID
    movie = db.query(Movie_model).filter(Movie_model.id == movie_id).first()
    if movie is None:
        logger.info(f"User '{current_user.username}' is attempting to update movie with ID={movie_id}")
    
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Movie not found"
        )
    if user.id != movie.user_id:
        logger.warning(f"User '{user.username}' is not authorized to update movie with ID={movie.id}. Forbidden action.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this movie"
        )
    db_description = db.query(Movie_model).filter(Movie_model.description == payload.description).first()
    if db_description:  # If a matching movie is found, raise a 406 error
        logger.warning("Listing failed for user, A movie with a similar description already exists.")
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Similar Movie already exists, Contact Support to make complaints."
        )
    movie.title = payload.title  # Update the movie's title
    movie.description = payload.description  # Update the movie's description
    movie.updated_at = datetime.now(timezone.utc)  # Update the movie's updated_at field to the current time
    db.commit()
    logger.info(f"Movie with ID={movie_id} successfully updated by user '{current_user.username}'")
    return movie
   

def delete_movie(db : db_dependency, movie_id : int, current_user : Login = Depends(get_current_user)):
    logger.info(f"User '{current_user.username}' is attempting to delete movie with ID={movie_id}")

    user = db.query(User).filter(User.username == current_user.username).first()
    movie = db.query(Movie_model).filter(Movie_model.id == movie_id).first()

    if movie is None:
        logger.warning(f"Movie with ID={movie_id} not found. Deletion operation aborted.")
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Movie not found"
        )
    if user.id != movie.user_id:
        logger.warning(f"User '{user.username}' is not authorized to modify movie with ID={movie.id}.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete this movie"
        )
    db.delete(movie)
    db.commit()
    logger.info(f"Movie with ID={movie_id} successfully deleted by user '{current_user.username}'")


def rate_movie(db : db_dependency, payload : RatingSchema, current_user : Login = Depends(get_current_user)):
    logger.info(f"User '{current_user.username}' is attempting to rate movie with ID={payload.movie_id}")

    movie = db.query(Movie_model).filter(Movie_model.id == payload.movie_id).first()
    user = db.query(User).filter(User.username == current_user.username).first()
    if movie is None:
        logger.error(f"Movie with ID {payload.movie_id} not found.")
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Movie not found"
        )
    # Check if the user has already rated the movie
    existing_rating = db.query(RatingModel).filter(
        RatingModel.movie_id == movie.id,
        RatingModel.user_id == user.id
    ).first()
    if existing_rating:  # If a rating already exists, raise a 400 error
        logger.warning(f"User has already rated movie with ID {movie.id}.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already rated this movie"
        )
    # Check if the rating is outside the acceptable range
    if payload.rating not in range(1, 10):
        logger.error(f"Invalid rating value: {payload.rating}. Must be an integer between 1 and 10.")
    
        raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = "Rating must be an integer between 0 and 11"
            ) # Return False if the rating is valid
    else:
        new_rating = RatingModel(
        user_id = user.id,
        movie_id = payload.movie_id,
        rating = payload.rating
            )
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        logger.info(f"User {current_user.username} successfully rated movie with ID {payload.movie_id}.")
        ratings = db.query(RatingModel).filter(RatingModel.movie_id == payload.movie_id).all()
        if not ratings:  # If no ratings are found, raise a 404 error
            logger.warning(f"No ratings found for movie with ID {payload.movie_id}.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No ratings found for this movie"
            )
        return ratings
        # return MovieService.average_rating(db, payload.movie_id)


def get_ratings(db : db_dependency, movie_id : int):
    logger.info(f"Fetching ratings for movie with ID={movie_id}")
    movie = db.query(Movie_model).filter(Movie_model.id == movie_id).first()
    if movie is None:
        logger.error(f"Movie with ID {movie_id} not found.")
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Movie not found"
        )
    else:
        ratings = db.query(RatingModel).filter(RatingModel.movie_id == movie_id).all()
        if not ratings:  # If no ratings are found, raise a 404 error
            logger.warning(f"No ratings found for movie with ID {movie_id}.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No ratings found for this movie"
            )
        # Extract rating values directly from the ORM objects
        rating_values = [rating.rating for rating in ratings]
        logger.info(f"Ratings for movie with ID {movie_id} retrieved successfully.")
        # Calculate the sum of rating values and the number of ratings
        total_rating = sum(rating_values)
        len_ratings = len(rating_values)
        return ratings
        # return MovieService.average_rating(db, movie_id)



def comment(db : db_dependency, payload : CommentSchema,  current_user : Login = Depends(get_current_user)):
    logger.info(f"User {current_user.username} is attempting to comment on movie with ID {payload.movie_id}.")
    user = db.query(User).filter(User.username == current_user.username).first()
    movie = db.query(Movie_model).filter(Movie_model.id == payload.movie_id).first()
    if movie is None:
        logger.error(f"Movie with ID {payload.movie_id} not found.")
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Movie not found"
        )
    logger.info(f"User {current_user.username} successfully commented on movie with ID {payload.movie_id}.")
    new_comment = CommentModel(
        user_id = user.id,
        movie_id = payload.movie_id,
        content = payload.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


def fetch_comments(db : db_dependency, movie_id : int, offset : int = 0, limit : int =10):
        # Query the database for a movie with the given movie ID
    movie = db.query(Movie_model).filter(Movie_model.id == movie_id).first()
    if movie is None:
        logger.error(f"Movie with ID {movie_id} not found.")
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Movie not found"
        )

    logger.info(f"Fetching comments for movie with ID={movie_id}")
    comments = db.query(CommentModel).filter(CommentModel.movie_id == movie_id).offset(offset).limit(limit).all()
    logger.info(f"Found {len(comments)} comments for movie with ID={movie_id}.")
    return comments

def reply_to_comment(db : db_dependency, payload : ReplyComment,  current_user : Login = Depends(get_current_user)):
    logger.info(f"User {current_user.username} is attempting to reply to comment with ID={payload.comment_id}.")
    user = db.query(User).filter(User.username == current_user.username).first()
    comment = db.query(CommentModel).filter(CommentModel.id == payload.comment_id).first()
    if comment is None:
        logger.error(f"Comment with ID {payload.comment_id} not found.")
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Comment not found"
        )
    movie = db.query(Movie_model).filter(Movie_model.id == payload.comment_id).first()
    logger.info(f"Movie with ID={movie.id} found. Creating reply.")
    new_reply = CommentModel(
                    user_id = user.id,
                    movie_id = movie.id, 
                    content = payload.content,
                    parent_id = payload.comment_id
                )
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)
    logger.info(f"Reply created successfully with ID={new_reply.id} by user ID={user.id} for comment ID={payload.comment_id}.")
    return new_reply           

  

  
    
   
    
   
