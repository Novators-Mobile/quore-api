from fastapi import FastAPI, Response, status, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.auth import hash, jwt_handler, jwt_bearer
from app.data import crud, schemas
from app.data.database import session, engine, base
import re, uvicorn, random, string

base.metadata.create_all(engine)

app = FastAPI(title="Quore API by Novatorsmobile",
              description="Only for devs)",
              version="0.9.9",
              docs_url='/api/docs',
              redoc_url='/api/redoc',
              openapi_url='/api/openapi.json')

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")

@app.post("/login")
async def login(response: Response, auth: schemas.AuthCreate, db: Session = Depends(get_db)):
    if not crud.get_user_by_email(db, auth.email):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error":"invalid user"}
    if not hash.verify(auth.password, crud.get_hashed(db, auth.email)):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error":"invalid user"}
    if not crud.get_verified(db, auth.email):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error":"not verified"}
    return {"access_token": jwt_handler.access_token(crud.get_id(db, auth.email)),
            "refresh_token": jwt_handler.refresh_token(crud.get_id(db, auth.email))}

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(response: Response, profile: schemas.ProfileCreate, auth: schemas.AuthCreate, db: Session = Depends(get_db)):
    if not crud.get_verified(db, auth.email):
        return {"code": "success"}
    if not re.match(r"\S+@\S+\.\S+" , auth.email):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error":"invalid email"}
    if crud.get_user_by_email(db, auth.email):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error": "user exists"}
    if sum(symbol.isdigit() for symbol in auth.password) == 0 or len(auth.password) < 8 or sum(symbol.isalpha() for symbol in auth.password) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error":"invalid password"}
    res = crud.create_profile(db, profile)
    generated_id = ''. join(random.choice(string.ascii_letters + string.digits) for i in range(128))
    while not crud.get_auth(db, generated_id):
        generated_id = ''. join(random.choice(string.ascii_letters + string.digits) for i in range(128))
    crud.create_auth(db, auth, res, generated_id)
    print(generated_id)
    return {"code": "success"}

@app.get("/test/{id}", status_code=status.HTTP_200_OK)
async def verify(response: Response, id: str, db: Session = Depends(get_db)):
    return {"test": "you're not allowed"}

@app.post("/cards", status_code=status.HTTP_200_OK)
async def cards(db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTBearer())):
    return crud.get_all_profiles(db)
