from fastapi import FastAPI, Response, status, Depends, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
import jinja2
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, MessageType
from app.auth import hash, jwt_handler, jwt_bearer, mail
from app.data import crud, schemas
from app.data.database import session, engine, base
import re, random, string

base.metadata.create_all(engine)

app = FastAPI(title="Quore API by Novatorsmobile",
              description="Only for devs)",
              version="0.9.9",
              root_path='/api')
mail = FastMail(mail.configuration)
jinja = jinja2.Environment()

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
    if not crud.get_email_verified(db, auth.email):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"error":"not verified"}
    return {"access_token": jwt_handler.access_token(crud.get_id(db, auth.email)),
            "refresh_token": jwt_handler.refresh_token(crud.get_id(db, auth.email))}

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(response: Response, background_tasks: BackgroundTasks, profile: schemas.ProfileCreate, auth: schemas.AuthCreate, db: Session = Depends(get_db)):
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
    generated_id = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(128))
    while crud.get_auth(db, generated_id) != None:
        print(crud.get_auth(db, generated_id))
        generated_id = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(128))
    crud.create_auth(db, auth, res, generated_id)
    with open('confirm.html', 'r') as file:
        template = jinja.from_string(file.read().rstrip())
    message = MessageSchema(
        subject="Подтверди свою почту",
        recipients=[auth.email],
        body=template.render(id=generated_id),
        subtype=MessageType.html)
    background_tasks.add_task(mail.send_message, message)
    return {"code": "success"}

@app.get("/verify/{id}", response_class=HTMLResponse)
async def verify(id: str, response: Response, db: Session = Depends(get_db)):
    if crud.get_auth(db, id):
        if not crud.get_verified(db, id):
            crud.verify_auth(db, id)
            return """Электронная почта подтверждена"""
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return """Почта уже была подтверждена"""
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return """Неправильная ссылка или почта не найдена"""
    
@app.get("/refresh")
async def refresh(token = Depends(jwt_bearer.JWTRefreshBearer())):
    id = jwt_handler.refresh_decode(token)['id']
    return {"access_token": jwt_handler.access_token(id)}

@app.get("/cards")
async def cards(db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    return crud.get_all_profiles(db)