from fastapi import FastAPI, Response, status, Depends
from sqlalchemy.orm import Session
from app.auth import hash, jwt_handler
from app.data import crud, models, schemas
from app.data.database import session, engine, base

base.metadata.create_all(engine)

app = FastAPI()

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/login")
async def login(response: Response, auth: schemas.AuthCreate, db: Session = Depends(get_db)):
    if not crud.get_user_by_email(db, auth.email):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error":"invalid user"}
    if not hash.verify(auth.password, crud.get_hashed(db, auth.email)):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error":"invalid user"}
    return {"access_token": jwt_handler.access_token(crud.get_id(db, auth.email)),
            "refresh_token": jwt_handler.refresh_token(crud.get_id(db, auth.email))}

@app.post("/api/register", status_code=status.HTTP_201_CREATED)
async def register(response: Response, profile: schemas.ProfileCreate, auth: schemas.AuthCreate, db: Session = Depends(get_db)):
    if sum(symbol.isdigit() for symbol in auth.password) == 0 or len(auth.password) < 8 or sum(symbol.isalpha() for symbol in auth.password) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error":"invalid password"}
    if crud.get_user_by_email(db, auth.email):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error": "user exists"}
    res = crud.create_profile(db, profile)
    crud.create_auth(db, auth, res)
    return {"code": "success"}