import jwt
from os import environ
from datetime import datetime, timedelta

ACCESS_SECRET = environ["JWT_ACCESS_SECRET"]
REFRESH_SECRET = environ["JWT_REFRESH_SECRET"]
ALGORITHM = environ["JWT_ALGORITHM"]
ACCESS_EXPIRE = timedelta(minutes=30)
REFRESH_EXPIRE = timedelta(days=7)

def access_token(id: int) -> str:
    payload = {"expire": (datetime.today() + ACCESS_EXPIRE).ctime(), "id": id}
    return jwt.encode(payload, ACCESS_SECRET, ALGORITHM)

def refresh_token(id: int) -> str:
    payload = {"expire": (datetime.today() + REFRESH_EXPIRE).ctime(), "id": id}
    return jwt.encode(payload, REFRESH_SECRET, ALGORITHM)