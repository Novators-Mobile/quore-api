from fastapi import FastAPI, status, Depends, BackgroundTasks, Query, Body
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import jinja2, datetime
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, MessageType
from os import environ
from app.auth import hash, jwt_handler, jwt_bearer, mail
from app.data import crud, schemas, media
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
        "name": "Галерея",
        "description": "Галерея изображений, загруженных пользователем в публичный доступ"
    },
    {
        "name": "Запросы для пользователей",
        "description": "Запросы для пользователя. Передаются через письма или ответы от сервера"
    },
    {
        "name": "Управление профилем",
        "description": "Управление своим профилем или получение информации о другом. Требуется авторизация по JWT-токену через заголовок Authorization: Bearer TOKEN"
    }
]

base.metadata.create_all(engine)

app = FastAPI(title="Quore API",
              description="Only for devs)",
              version="0.9.9",
              contact={
                  "name": "Novators Mobile",
                  "url": "https://github.com/Novators-Mobile",
                  "email": "admin@novatorsmobile.ru"
              },
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
    """
    Авторизация пользователя по почте и паролю. Возвращает JWT-токены для дальнейших запросов
    """
    if not crud.get_user_by_email(db, auth.email):
        return JSONResponse({"error":"invalid user"}, status.HTTP_401_UNAUTHORIZED)
    if not hash.verify(auth.password, crud.get_hashed(db, auth.email)):
        return JSONResponse({"error":"invalid user"}, status.HTTP_401_UNAUTHORIZED)
    if not crud.get_email_verified(db, auth.email):
        return JSONResponse({"error":"invalid user"}, status.HTTP_401_UNAUTHORIZED)
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
    """
    Регистрация пользователя. После регистрации на указанную почту отправляется письмо с ссылкой на подтверждение (см. /verify) 
    Для успешной регистрации поля должны соответствовать следующим требованиям:
    1. Почта должна соответствовать обычному формату
    2. Почта не должна быть уже зарегистрирована на другого пользователя
    3. Пароль должен содержать хотя бы одну цифру, одну английскую букву, и быть длиной не менее 8 символов
    4. Возраст пользователя должен быть не меньше 18 лет
    """
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
    if int(environ["DEBUG"]):
        crud.verify_auth(db, generated_id)
    else:
        background_tasks.add_task(mail.send_message, message)
    return {"result": "success"}

@app.get("/verify/{id}", tags=["Запросы для пользователей"], response_class=HTMLResponse, responses={
    410: {"description": "Электронная почта подтверждена ранее", "content": {
        "text/html": {
            "example": "Почта уже была подтверждена"
        }
    }},
    400: {"description": "Пользователь не регистрировался или в ссылке ошибка", "content": {
        "text/html": {
            "example": "Неправильная ссылка или почта не найдена"
        }
    }},
    200: {"description": "Электронная почта подтверждена", "content": {
        "text/html": {
            "example": "Электронная почта подтверждена"
        }
    }}
})
async def verify(id: str, db: Session = Depends(get_db)):
    """
    Запрос посылается от пользователя при переходе по ссылке из письма (см. /register)
    Возвращает HTML с текстом о статусе подтверждения
    """
    if crud.get_auth(db, id):
        if not crud.get_verified(db, id):
            crud.verify_auth(db, id)
            return HTMLResponse("""Электронная почта подтверждена""", status.HTTP_200_OK)
        else:
            return HTMLResponse("""Почта уже была подтверждена""", status.HTTP_410_GONE)
    else:
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
async def resend(background_tasks: BackgroundTasks, email: str, db: Session = Depends(get_db)):
    """
    Запрос повторной отправки письма на почту. Можно вызвать только раз в 45 секунд.
    """
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

@app.get("/refresh", tags=["Авторизация"], responses={
    200: {"description": "Токены обновлены", "content": {
        "application/json": {
            "example": {"access_token": "access token",
                        "refresh_token": "refresh token"}
        }
    }}
})
async def refresh(token = Depends(jwt_bearer.JWTRefreshBearer())):
    """
    Обновление access token и refresh token. Требуется авторизация по refresh token через заголовок Authorization: Bearer TOKEN
    """
    return {"access_token": jwt_handler.access_token(jwt_handler.refresh_decode(token)),
            "refresh_token": jwt_handler.refresh_token(jwt_handler.refresh_decode(token))}

@app.get("/cards", tags=["Рекомандации"], responses={
    200: {"description": "Карточки пользователей", "content": {
        "application/json": {
            "example": [
                {
                    "id": 0,
                    "name": "Ivan Ivanov",
                    "age": 18,
                    "status": "Love cats and FastAPI"
                },
                {
                    "id": 1,
                    "name": "Peter Petrov",
                    "age": 20,
                    "status": "Never gonna give you up"
                }
            ]
        }
    }}
})
async def cards(agefrom: int = Query(None, description="Старше"), ageto: int = Query(None, description="Младше"), sex: str = Query(None, description="Пол"),  db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    """
    Выдача рекомендации карточек. На данный момент отображаются все пользователи за исключением авторизованного.
    """
    if not agefrom:
        agefrom = 0
    if not ageto:
        ageto = 2000
    if sex:
        return crud.get_all_profiles_by_sex(db, jwt_handler.access_decode(token)['id'], agefrom, ageto, sex)
    else:
        return crud.get_all_profiles(db, jwt_handler.access_decode(token)['id'], agefrom, ageto)
    
@app.get("/like", tags=["Рекомандации"], responses={
    200: {"description": "Лайки пользователя. Выводится неправильно, дорабатывается!!!", "content": {
        "application/json": {
            "example": [
                {
                    "id": 0,
                    "target": 1
                },
                {
                    "id": 1,
                    "target": 5
                }
            ]
        }
    }}
})
def get_likes(db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    """
    Лайки авторизованного пользователя. Выводится неправильно, дорабатывается!!!
    """
    return crud.get_likes(db, jwt_handler.access_decode(token)['id'])

@app.post("/like", tags=["Рекомандации"], responses={
    200: {"description": "Лайк создан", "content": {
        "application/json": {
            "example": {"result": "success"}
        }
    }},
    201: {"description": "Лайк оказался совместным - мэтч", "content": {
        "application/json": {
            "example": {"result": "match"}
        }
    }},
    202: {"description": "Лайк был создан ранее, лайк снимаем", "content": {
        "application/json": {
            "example": {"result": "deleted"}
        }
    }},
    404: {"description": "Пользователь не найден", "content": {
        "application/json": {
            "example": {"error": "user not found"}
        }
    }}
})
async def like_profile(id: int = Query(..., description="ID профиля"), db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    """
    Поставить лайк пользователю. Если лайк уже поставлен - лайк удаляется. Если был дизлайк - удаляется дизлайк и ставится лайк. При наличии лайка от другого пользователя сообщает о мэтче.
    """
    if not crud.get_profile(db, id):
        return JSONResponse({"error": "user not found"}, status.HTTP_404_NOT_FOUND)
    initiator = jwt_handler.access_decode(token)['id']
    if crud.get_like(db, initiator, id):
        crud.delete_like(db, initiator, id)
        return JSONResponse({"result": "deleted"}, status.HTTP_202_ACCEPTED)
    if crud.get_like(db, id, initiator):
        crud.match(db, id, initiator)
        return JSONResponse({"result": "match"}, status.HTTP_200_OK)
    else:
        if crud.get_dislike(db, initiator, id):
            crud.delete_dislike(db, initiator, id)
        crud.like(db, initiator, id)
        return JSONResponse({"result": "liked"}, status.HTTP_201_CREATED)

@app.get("/dislike", tags=["Рекомандации"], responses={
    200: {"description": "Дизлайки пользователя", "content": {
        "application/json": {
            "example": [
                {
                    "id": 0,
                    "target": 1
                },
                {
                    "id": 1,
                    "target": 5
                }
            ]
        }
    }}
})
async def get_dislikes(db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    """
    Дизлайки авторизованного пользователя
    """
    return crud.get_dislikes(db, jwt_handler.access_decode(token)['id'])

@app.post("/dislike", tags=["Рекомандации"], responses={
    201: {"description": "Дизлайк создан", "content": {
        "application/json": {
            "example": {"result": "disliked"}
        }
    }},
    202: {"description": "Дизлайк удален", "content": {
        "application/json": {
            "example": {"result": "deleted"}
        }
    }},
    404: {"description": "Пользователь не найден", "content": {
        "application/json": {
            "example": {"error": "user not found"}
        }
    }}
})
async def dislike_profile(id: int = Query(..., description="ID профиля"), db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    """
    Поставить профилю дизлайк. Если был лайк - удаляется лайк и ставится дизлайк. Если дизлайк уже поставлен - дизлайк удаляется.
    """
    if not crud.get_profile(db, id):
        return JSONResponse({"error": "user not found"}, status.HTTP_404_NOT_FOUND)
    if crud.get_dislike(db, jwt_handler.access_decode(token)['id'], id):
        crud.delete_dislike(db, jwt_handler.access_decode(token)['id'], id)
        return JSONResponse({"result": "deleted"}, status.HTTP_202_ACCEPTED)
    if crud.get_like(db, jwt_handler.access_decode(token)['id'], id):
        crud.delete_like(db, jwt_handler.access_decode(token)['id'], id)
    crud.dislike(db, jwt_handler.access_decode(token)['id'], id)
    return JSONResponse({"result": "disliked"}, status.HTTP_201_CREATED)

@app.post("/images", tags=["Галерея"], responses={
    200: {"description": "Изображение успешно загружен", "content": {
        "application/json": {
            "example": {"result": "success"}
        }
    }}
})
async def post_image(image: bytes = Body(None, description="Изображение", media_type="image/*"), db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    """
    Загрузить изображение в публичный доступ
    """
    id = jwt_handler.access_decode(token)['id']
    media.upload_image(image, id, crud.add_image(db, id))
    return {"result": "success"}

@app.get("/images", tags=["Галерея"], responses={
    200: {"description": "Все изображения пользователя", "content": {
        "application/json": {
            "example": [
                "https://novatorsmobile.ru/s3/images/1_1.jpg?AWSAccessKeyId=quoreapi&Signature=YW50b24gbG9iYW5vdg==&Expires=1168335660",
                "https://novatorsmobile.ru/s3/images/1_2.jpg?AWSAccessKeyId=quoreapi&Signature=YWxleGFuZHJhIHNhdmVsZXZh&Expires=1168335660",
                "https://novatorsmobile.ru/s3/images/1_3.jpg?AWSAccessKeyId=quoreapi&Signature=YW5hc3Rhc2lhIGJvYmluYQ==&Expires=1168335660",
            ]
        }
    }},
    404: {"description": "Пользователь не существует", "content": {
        "application/json": {
            "example": {"error": "user not found"}
        }
    }}
})
async def get_images(id: int = Query(None, description="ID профиля. При отсутствии параметра возвращается информация об авторизованном пользователе"), db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    """
    Выдача всех изображений, выложенным пользователем в публичный доступ
    """
    if id == None:
        id = jwt_handler.access_decode(token)['id']
    result = crud.get_profile(db, id)
    if not result:
        return JSONResponse({"error": "user not found"}, status.HTTP_404_NOT_FOUND)
    return media.get_images(crud.get_images(db, id))

@app.delete("/images", tags=["Галерея"], responses={
    200: {"description": "Удаление изображения", "content": {
        "application/json": {
            "example": {"result": "success"}
        }
    }},
    403: {"description": "Изображение не существует или не принадлежит пользователю", "content": {
        "application/json": {
            "example": {"error": "no access"}
        }
    }}
})
async def delete_image(file: str = Query(..., description="Имя файла"), db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    """
    Удаление конкретного изображения
    """
    id = jwt_handler.access_decode(token)['id']
    if file in crud.get_images(db, id):
        media.delete_image(file)
        crud.delete_image(db, id, file)
        return {"result": "success"}
    else:
        return JSONResponse({"error": "no access"}, status.HTTP_403_FORBIDDEN)

@app.get("/profile", tags=["Управление профилем"], responses={
    200: {"description": "Информация о профиле", "content": {
        "application/json": {
            "example": {
                "id": 0,
                "name": "Ivan Ivanov",
                "about": "Somebody once told me the world is gonna roll me. I ain't the sharpest tool in the shed.",
                "age": 18,
                "status": "Love cats and FastAPI",
                "avatar": "https://novatorsmobile.ru/s3/images/0.jpg?AWSAccessKeyId=quoreapi&Signature=Tk9WQVRPUlNNT0JJTEU=&Expires=1168335660"
            }
        }
    }},
    404: {"description": "Профиль не найден", "content": {
        "application/json": {
            "example": {"error": "user not found"}
        }
    }}
})
async def profile_get(id: int = Query(None, description="ID профиля. При отсутствии параметра возвращается информация об авторизованном пользователе"), db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    """
    Полная информация о профиле
    """
    if id == None:
        id = jwt_handler.access_decode(token)['id']
    result = crud.get_profile(db, id)
    if not result:
        return JSONResponse({"error": "user not found"}, status.HTTP_404_NOT_FOUND)
    return result

@app.patch("/profile", tags=["Управление профилем"], responses={
    200: {"description": "Информация обновлена", "content": {
        "application/json": {
            "example": {"result": "success"}
        }
    }}
})
async def profile_edit(name: str = Query(None, description="Имя пользователя"), status: str = Query(None, description="Отображаемый статус"), about: str = Query(None, description="О себе"), avatar: bytes = Body(None, description="Аватар"), db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    """
    Изменение информации профиля авторизованного пользователя
    """
    id = jwt_handler.access_decode(token)['id']
    if name != None:
        crud.change_name(db, id, name)
    if status != None:
        crud.change_status(db, id, status)
    if about != None:
        crud.change_about(db, id, about)
    if avatar != None:
        crud.create_avatar(db, id)
        media.upload_avatar(avatar, id)
    return {"result": "success"}

@app.delete("/profile", tags=["Управление профилем"], responses={
    200: {"description": "Профиль удален", "content": {
        "application/json": {
            "example": {"result": "success"}
        }
    }},
    401: {"description": "Пароль или токен неправильные", "content": {
        "application/json": {
            "example": {"error": "not verified"}
        }
    }},
})
async def profile_delete(password: str = Query(..., description="Пароль пользователя"), db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    """
    Удаление профиля и другой связанной информации
    """
    id = jwt_handler.access_decode(token)['id']
    auth = crud.get_auth_profile(db, jwt_handler.access_decode(token)['id'])
    if auth:
        if not hash.verify(password, auth.hashed):
            return JSONResponse({"error": "not verified"}, status.HTTP_401_UNAUTHORIZED)
    else:
        return JSONResponse({"error": "not verified"}, status.HTTP_401_UNAUTHORIZED)
    media.delete_all_images(crud.get_images(db, id))
    media.delete_avatar(id)
    crud.delete_user(db, id)
    return JSONResponse({"result": "success"}, status.HTTP_200_OK)

@app.get("/gdpr", tags=["Управление профилем"], responses={
    200: {"description": "Информация отправленна на электронную почту", "content": {
        "application/json": {
            "example": {"result": "success"}
        }
    }},
    401: {"description": "Пароль или токен неправильные", "content": {
        "application/json": {
            "example": {"error": "not verified"}
        }
    }},
})
async def gdpr_request(background_tasks: BackgroundTasks, password: str = Query(..., description="Пароль пользователя"), db: Session = Depends(get_db), token = Depends(jwt_bearer.JWTAccessBearer())):
    """
    Запрос информации о пользователе. Требуется в соответствии с федеральным законом №152-ФЗ "О персональных данных" Российской федерации и Общим регламентом защиты персональных данных (GDPR) Европейского союза
    """
    auth = crud.get_auth_profile(db, jwt_handler.access_decode(token)['id'])
    profile = crud.get_profile(db, jwt_handler.access_decode(token)['id'])
    if auth:
        if not hash.verify(password, auth.hashed):
            return JSONResponse({"error": "not verified"}, status.HTTP_401_UNAUTHORIZED)
    else:
        return JSONResponse({"error": "not verified"}, status.HTTP_401_UNAUTHORIZED)
    with open('gdpr.html', 'r') as file:
        template = jinja.from_string(file.read().rstrip())
    likes = crud.get_all_likes_name_users(db, jwt_handler.access_decode(token)['id'])
    dislikes = crud.get_all_dislikes_name_users(db, jwt_handler.access_decode(token)['id'])
    message = MessageSchema(
        subject="Ваш запрос на получение информации",
        recipients=[auth.email],
        body=template.render(name=profile.name, birth=profile.birth, age=profile.age, sex=profile.sex, about=profile.about, status=profile.status, email=auth.email, sent=auth.sent, likes=likes, dislikes=dislikes),
        subtype=MessageType.html)
    background_tasks.add_task(mail.send_message, message)
    return JSONResponse({"result": "success"}, status.HTTP_200_OK)