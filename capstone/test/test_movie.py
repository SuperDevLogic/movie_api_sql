import os

from dotenv import load_dotenv

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient
from fastapi  import status

from capstone.database import Base, get_db
from capstone.main import app

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")


engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

  # Clean up the database after tests
@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
  

@pytest.mark.parametrize("username, email, password", [("username", "test@example.com", "testpassword")])
def test_list_movies(client, setup_database, username, email, password):
       #First Sign up a user
    initial1 = client.post(
        "/user/signup",
        json={"username": username, "email": email, "password": password}
    )
    
    assert initial1.status_code == status.HTTP_201_CREATED
    initial2 = client.post("/user/auth/login", data={"username": username, "password": password})
    assert initial2.status_code == 200
    token = initial2.json()["access_token"]

    # Then, create a movie
    movie_data = {"title": "Test Movie", "description": "Test Description"}
    response = client.post("/movie", json=movie_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data.get("description") == "Test Description"
    assert data.get("title") == "Test Movie"
    assert data.get("id") == 1




@pytest.mark.parametrize("username, password", [("testuser", "testpassword")])
def test_fetch_movies(client, setup_database, username, password):
    response = client.get("/movie")
    assert response.status_code == status.HTTP_200_OK
    assert type(response.json()) == list
    assert response.json()[0]["title"] == "Test Movie"
    assert response.json()[0]["description"] == "Test Description"
    assert response.json()[0]["release_date"] == f"{response.json()[0].get('release_date')}"
    assert response.json()[0]["updated_at"] == f"{response.json()[0].get('updated_at')}"

@pytest.mark.parametrize("username, password,", [("username", "testpassword")])
def test_fetch_movies_by_id(client, setup_database, username, password):
    response = client.get("/movie/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("title") == "Test Movie"
    assert response.json().get("description") == "Test Description"
    assert response.json() == {
        "id": response.json()['id'],
        "title": "Test Movie",
        "description": "Test Description",
        "release_date": f"{response.json().get('release_date')}",
        "updated_at": f"{response.json().get('updated_at')}"
    }

@pytest.mark.parametrize("username, password", [("username", "testpassword")])
def test_fetch_movies_not_found(client, setup_database, username, password):
    response = client.get("/movie/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("detail") == "Movie not found"


@pytest.mark.parametrize("username, password", [("username", "testpassword")])
def test_update_movie(client, setup_database, username, password):
    response = client.post("/user/auth/login", data={"username": username, "password": password})
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]

    movie_data = {"title": "Updated Test Movie", "description": "Updated Test Description"}
    response = client.put("/movie/1", json=movie_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json().get("title") == "Updated Test Movie"
    assert response.json().get("description") == "Updated Test Description"
    assert response.json() == {
       "id": response.json()['id'],
        "title": "Updated Test Movie",
        "description": "Updated Test Description",
        "release_date": f"{response.json()['release_date']}",
        "updated_at": f"{response.json()['updated_at']}"
    }




@pytest.mark.parametrize("username, password", [("username", "testpassword")])
def test_delete_movie_not_found(client, setup_database, username, password):
    response = client.post("/user/auth/login", data={"username": username, "password": password})
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    response = client.delete("/movie/999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("detail") == "Movie not found"


@pytest.mark.parametrize("username, password", [("username", "testpassword")])
def test_rate_movie(client, setup_database, username, password):
    # Login a user
    response = client.post("/user/auth/login", data={"username": username, "password": password})
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
            # Then create a movie with the user
    movie_data = {"title": "Test Movie", "description": "Test Movie to rate Description"}
    response = client.post("/movie", json=movie_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_201_CREATED
    id_movie = response.json().get('id')
    assert type(id_movie) == int

    #Rate the movie
    response = client.post(
        "/movie/{movie_id}/rate",
        json={
            "movie_id" : id_movie,
            "rating": 6.0
        },
        headers={
            "Authorization": f"Bearer {token}",
            "content_type": "application/json"
        }
    ) 

    assert response.status_code == status.HTTP_201_CREATED
    
                
@pytest.mark.parametrize("username, password", [("username", "testpassword")])
def test_user_already_rated_movie(client, setup_database, username, password):
    # First Login a user
    response = client.post("/user/auth/login", data={"username": username, "password": password})
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
        #Rate the movie id == 2
    response = client.post(
        "/movie/{movie_id}/rate",
        json={
            "movie_id" : 2,
            "rating": 6.0
        },
        headers={
            "Authorization": f"Bearer {token}",
            "content_type": "application/json"
        }
    ) 
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json().get("detail") == "You have already rated this movie"
    


@pytest.mark.parametrize("username, password", [("username", "testpassword")])
def test_movieToBe_rated_not_found(client, setup_database, username, password):
    # Login a user
    response = client.post("/user/auth/login", data={"username": username, "password": password})
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    # Then attempt to rate a non-existent movie
    response = client.post(
        "/movie/999/rate",
        json={
            "movie_id" : 999,
            "rating": 6.0
        },
        headers={
            "Authorization": f"Bearer {token}",
            "content_type": "application/json"
        }
    )   
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("detail") == "Movie not found"


    

@pytest.mark.parametrize("username, password", [("username", "testpassword")])
def test_toGet_ratings_not_found(client, setup_database, username, password):
    # Attempt to get the ratings of a non-existent movie
    response = client.get(f"/movie/999/ratings")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("detail") == "Movie not found"

@pytest.mark.parametrize("username, password", [("username", "testpassword")])
def test_comment_on_movie(client, setup_database, username, password):
    # Login a user
    response = client.post("/user/auth/login", data={"username": username, "password": password})
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    # Then create a movie with the user
    movie_data = {"title": "Test Movie", "description": "Test Movie to comment Description"}
    response = client.post("/movie", json=movie_data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_201_CREATED
    id_movie = response.json().get('id')
    assert type(id_movie) == int
    
    # Comment on the movie
    response = client.post(
        "/movie/3/comment",
        json={
            "movie_id" : 3,
            "content": "Great"
        },
        headers={
            "Authorization": f"Bearer {token}",
            "content_type": "application/json"
        }
    )  
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() =={
                    "content" : "Great",
                    "movie_id" : 3,
                    'parent_id': None
            }
    
@pytest.mark.parametrize("username, password", [("username", "testpassword")])
def test_movieToBe_commented_not_found(client, setup_database, username, password):
    # Login a user
    response = client.post("/user/auth/login", data={"username": username, "password": password})
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    # Then attempt to comment on a non-existent movie
    response = client.post(
        "/movie/999/comment",
        json={
            "movie_id" : 999,
            "content": "Great"
        },
        headers={
            "Authorization": f"Bearer {token}",
            "content_type": "application/json"
        }
    )   
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("detail") == "Movie not found"

@pytest.mark.parametrize("username, password", [("username", "testpassword")])
def test_get_comments_onMovie(client, setup_database, username, password):
    response = client.get(f"/movie/3/comments")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json() == [
            {
                "movie_id": 3,
                "parent_id": None,
                "content": "Great",
                "id": 1,
                "user_id": 1
            }
    ]
    
@pytest.mark.parametrize("username, password", [("username", "testpassword")])
def test_comment_to_reply_notFound(client, setup_database, username, password):
    #Login user
    response = client.post("/user/auth/login", data={"username": username, "password": password})
    assert response.status_code == status.HTTP_200_OK
    token = response.json()["access_token"]
    #Try to reply to a comment that does not exist
    response = client.post(
        "/movie/999999/reply",
        json={
            "comment_id" : 999999,
            "content": "Great"
        },
        headers={
            "Authorization": f"Bearer {token}",
            "content_type": "application/json"
        }
    )
  
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json().get("detail") == "Comment not found"




    






                





