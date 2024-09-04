from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from capstone.database import db_dependency
from capstone.user.schema import SignUpModel
from capstone.auth.hash import Hash
from capstone.user.models import User 
from capstone.auth.jwt import create_access_token

from capstone.logger import get_logger

# Enable sending logs from the standard Python logging module to Sentry

logger = get_logger(__name__)


def sign_up(db : db_dependency, payload : SignUpModel):
    logger.info("Creating a new user: %s", payload.username)
    db_email = db.query(User).filter(User.email == payload.email).first()
    if db_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    db_username = db.query(User).filter(User.username == payload.username).first()
    if db_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
    
    hashed_password = Hash.bcrypt(payload.password)
    new_user = User(
        email = payload.email,
        username = payload.username,
        password = hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"User {payload.username} has been created")
    return new_user


def login(db : db_dependency, payload : OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Login attempt for user: {payload.username}")

        # Fetch the user, and handle "user not found" error
    user = db.query(User).filter(User.username == payload.username).first()
    if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid credentials"
            )

    logger.info(f"User found: {payload.username}")
        # Verify the password, and handle "incorrect password" error
    if not Hash.verify(payload.password, user.password):
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )
    logger.info(f"Password verified for user: {payload.username}")

    access_token =  create_access_token(data = {
        "sub" : user.username
    })
    logger.info(f"User {payload.username} logged in successfully")
    
    return {
        "access_token" : access_token,
        "token_type" : "bearer"
    }