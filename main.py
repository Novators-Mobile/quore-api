from fastapi import FastAPI, Response, status, Depends, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import jinja2, datetime
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, MessageType
from app.auth import hash, jwt_handler, jwt_bearer, mail
from app.data import crud, schemas
from app.data.database import session, engine, base
import re, random, string

tags_metadata = [
    {
        "name": "Авторизация",
        "description": "Запросы для регистрации и авторизации"
    },
    {
        "name": "Рекомандации",
        "description": "Запросы для работы с основным экраном рекомендаций. Требуется авторизация по JWT-токену через заголовок Authorization: Bearer TOKEN"
    },
    {
        "name": "Запросы для пользователей",
        "description": "Запросы для пользователя. Передаются через письма или ответы от сервера"
    }
]

base.metadata.create_all(engine)

app = FastAPI(title="Quore API by Novatorsmobile",
              description="Only for devs)",
              version="0.9.9",
              openapi_tags=tags_metadata,
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

@app.get("/authors.png", include_in_schema=False)
async def favicon():
    return FileResponse("authors.png")

@app.get("/logo.png", include_in_schema=False)
async def favicon():
    return FileResponse("logo.png")

@app.get("/QUORE.png", include_in_schema=False)
async def favicon():
    return FileResponse("QUORE.png")

@app.post("/login", tags=["Авторизация"], responses={
    401: {"description": "Пользователь не существует или неправильный пароль", "content": {
        "application/json": {
            "example": {"error":"invalid user"}
        }
    }},
    401: {"description": "Электронная почта пользователя не подтверждена", "content": {
        "application/json": {
            "example": {"error":"not verified"}
        }
    }},
    200: {"description": "Успешный вход", "content": {
        "application/json": {
            "example": {"access_token": "access token",
                        "refresh_token": "refresh token"}
        }
    }}
})
async def login(auth: schemas.AuthCreate, db: Session = Depends(get_db)):
    if not crud.get_user_by_email(db, auth.email):
        return JSONResponse({"error":"invalid user"}, status.HTTP_401_UNAUTHORIZED)
    if not hash.verify(auth.password, crud.get_hashed(db, auth.email)):
        return JSONResponse({"error":"invalid user"}, status.HTTP_401_UNAUTHORIZED)
    if not crud.get_email_verified(db, auth.email):
        return JSONResponse({"error":"not verified"}, status.HTTP_401_UNAUTHORIZED)
    return {"access_token": jwt_handler.access_token(crud.get_id(db, auth.email)),
            "refresh_token": jwt_handler.refresh_token(crud.get_id(db, auth.email))}

@app.post("/register", status_code=status.HTTP_201_CREATED, tags=["Авторизация"], responses={
    401: {"description": "Пользователь с данной электронной почтой уже существует", "content": {
        "application/json": {
            "example": {"error": "user exists"}
        }
    }},
    400: {"description": "Пароль не соответствует требованиям безопасности", "content": {
        "application/json": {
            "example": {"error": "invalid password"}
        }
    }},
    400: {"description": "Возраст пользователя меньше 18 лет", "content": {
        "application/json": {
            "example": {"error": "adults only"}
        }
    }},
    400: {"description": "Электронная почта неправильно введена (без @ или домена)", "content": {
        "application/json": {
            "example": {"error": "invalid email"}
        }
    }},
    201: {"description": "Успешная регистрация. Возвращает ссылку на повторную отправку письма", "content": {
        "application/json": {
            "example": {"result": "success"}
        }
    }}
})
async def register(background_tasks: BackgroundTasks, profile: schemas.ProfileCreate, auth: schemas.AuthCreate, db: Session = Depends(get_db)):
    if not re.match(r"\S+@\S+\.\S+" , auth.email):
        return JSONResponse({"error": "invalid email"}, status.HTTP_400_BAD_REQUEST)
    if crud.get_user_by_email(db, auth.email):
        return JSONResponse({"error": "user exists"}, status.HTTP_401_UNAUTHORIZED)
    if sum(symbol.isdigit() for symbol in auth.password) == 0 or len(auth.password) < 8 or sum(symbol.isalpha() for symbol in auth.password) == 0:
        return JSONResponse({"error": "invalid password"}, status.HTTP_400_BAD_REQUEST)
    if datetime.date.today().year - profile.birth.year - ((datetime.date.today().month, datetime.date.today().day) < (profile.birth.month, profile.birth.day)) < 18:
        return JSONResponse({"error": "adults only"}, status.HTTP_400_BAD_REQUEST)
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
    return {"result": "success"}

@app.get("/verify/{id}", tags=["Запросы для пользователей"], response_class=HTMLResponse)
async def verify(id: str, response: Response, db: Session = Depends(get_db)):
    if crud.get_auth(db, id):
        if not crud.get_verified(db, id):
            crud.verify_auth(db, id)
            return HTMLResponse("""Электронная почта подтверждена""", status.HTTP_200_OK)
        else:
            return HTMLResponse("""Почта уже была подтверждена""", status.HTTP_400_BAD_REQUEST)
    else:
        response.status_code = status.HTTP_404_NOT_FOUND
        return HTMLResponse("""Неправильная ссылка или почта не найдена""", status.HTTP_400_BAD_REQUEST)
     
@app.get("/resend/{email}", tags=["Авторизация"], responses={
    404: {"description": "Пользователь не существует", "content": {
        "application/json": {
            "example": {"error":"invalid user"}
        }
    }},
    400: {"description": "Электронная почта пользователя уже подтверждена", "content": {
        "application/json": {
            "example": {"error": "user verified"}
        }
    }},
    425: {"description": "Между предыдущим запросом письма прошло меньше 45 секунд", "content": {
        "application/json": {
            "example": {"error": "timeout"}
        }
    }},
    200: {"description": "Новое письмо отправлено", "content": {
        "application/json": {
            "example": {"result": "success"}
        }
    }}
})
async def resend(email: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not crud.get_user_by_email(db, email):
        return JSONResponse({"error": "invalid user"}, status.HTTP_404_NOT_FOUND)
    if crud.get_email_verified(db, email):
        return JSONResponse({"error": "user verified"}, status.HTTP_400_BAD_REQUEST)
    if (datetime.datetime.today() - crud.get_email_sent(db, email)).total_seconds() < 45:
        return JSONResponse({"error": "timeout"}, status.HTTP_425_TOO_EARLY)
    generated_id = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(128))
    while crud.get_auth(db, generated_id) != None:
        print(crud.get_auth(db, generated_id))
        generated_id = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(128))
    crud.change_auth_id(db, email, generated_id)
    with open('confirm.html', 'r') as file:
        template = jinja.from_string(file.read().rstrip())
    message = MessageSchema(
        subject="Подтверди свою почту",
        recipients=[email],
        body=template.render(id=generated_id),
        subtype=MessageType.html)
    background_tasks.add_task(mail.send_message, message)
    crud.change_auth_sent(db, email, datetime.datetime.today())
    return {"result": "success"}

@app.get("/refresh", tags=["Авторизация"])
async def refresh(token = Depends(jwt_bearer.JWTRefreshBearer())):
    id = jwt_handler.refresh_decode(token)['id']
    return {"access_token": jwt_handler.access_token(id)}

@app.get("/cards", tags=["Рекомандации"])
async def cards(db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    return crud.get_all_profiles(db, jwt_handler.access_decode(token)['id'])