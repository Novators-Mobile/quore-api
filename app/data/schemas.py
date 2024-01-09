from pydantic import BaseModel
from datetime import date

class ProfileCreate(BaseModel):
    name: str
    birth: date
    sex: str

    class Config:
        from_attributes = True

class Profile(BaseModel):
    id: int

class AuthCreate(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True