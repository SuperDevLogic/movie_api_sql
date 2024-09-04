# FastAPI Movie App with PostgreSQL

This project is a movie application built with FastAPI and PostgreSQL. Authenticated users can perform CRUD (Create, Read, Update, Delete) operations on movies, as well as comment on and rate movies. The application is designed to be a robust, scalable, and easy-to-use platform for managing movies and user interactions.

## Features

- **User Authentication**: Secure user authentication using JWT tokens.
- **CRUD Operations**: Full CRUD functionality for managing movies.
- **Comments**: Users can comment on movies.
- **Ratings**: Users can rate movies.
- **PostgreSQL Database**: Persistent storage using PostgreSQL.

## Requirements

- Python 3.8+
- PostgreSQL
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- JWT (PyJWT)
- Uvicorn

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SuperDevLogic/movie_api_sql.git
   cd fastapi-movie-app
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```



5. **Apply database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Run the application:**
   ```bash
   uvicorn main:app --reload
   ```

## Project Structure

- `main.py`: The entry point of the application. It initializes the FastAPI app, sets up routes, and handles middleware.
- `models.py`: Defines the SQLAlchemy models for the database.
- `schemas.py`: Pydantic models for data validation and serialization.
- `crud.py`: Contains the CRUD operations for interacting with the database.
- `auth.py`: Handles user authentication, including JWT token creation and validation.
- `routes/`: Contains the FastAPI route definitions for movies, comments, and ratings.
- `alembic/`: Database migration directory.
- `tests/`: Directory containing unit and integration tests.

## API Endpoints

### Authentication
- **POST /auth/register**: Register a new user.
- **POST /auth/login**: Login and receive a JWT token.

### Movies
- **GET /movies/**: Get a list of all movies.
- **POST /movies/**: Create a new movie (authenticated users).
- **GET /movies/{movie_id}**: Get details of a specific movie.
- **PUT /movies/{movie_id}**: Update an existing movie (authenticated users).
- **DELETE /movies/{movie_id}**: Delete a movie (authenticated users).

### Comments
- **POST /movies/{movie_id}/comments/**: Add a comment to a movie (authenticated users).
- **GET /movies/{movie_id}/comments/**: Get all comments for a specific movie.

### Ratings
- **POST /movies/{movie_id}/rate/**: Rate a movie (authenticated users).
- **GET /movies/{movie_id}/ratings/**: Get all ratings for a specific movie.

## Authentication

Authentication is handled using JWT (JSON Web Tokens). Upon successful login, a token is returned, which must be included in the `Authorization` header of subsequent requests as follows:

```bash
Authorization: Bearer <your_token>
```

## Database Migrations

Database migrations are managed using Alembic. To create a new migration after modifying models, run:

```bash
alembic revision --autogenerate -m "your message here"
```

Then, apply the migration with:

```bash
alembic upgrade head
```

## Testing

Tests are located in the `tests/` directory. To run the tests, use:

```bash
pytest
```

## Contributing

If you'd like to contribute to this project, please fork the repository and submit a pull request. We welcome all improvements, whether they are documentation, code quality, or new features.



---

This README provides a basic overview of how to get started with the FastAPI movie app. For more detailed information, please refer to the documentation or explore the codebase.