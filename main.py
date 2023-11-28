from fastapi import FastAPI, Response, status
from app.auth import hash

app = FastAPI()

@app.get("/api/login")
def login(response: Response, password: str, hashed: str):
    if not hash.verify(password, hashed):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error":"invalid user"}
    return {"code":"success"}

@app.post("/api/register")
def register(response: Response, email: str, name: str, password: str):
    if sum(symbol.isdigit() for symbol in password) == 0 or len(password) < 8 or sum(symbol.isalpha() for symbol in password) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error":"invalid password"}
    return {"code":"success"}