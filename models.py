from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    age: Optional[int] = Field(None, ge=1, le=150, description="Возраст пользоваетля")
    is_subscribed: Optional[bool] = Field(False, description="Подписка на рассылку")

class LoginRequest(BaseModel):
    username: str
    password: str


class UserProfile(BaseModel):
    user_id: str
    username: str
    email: str


class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias="User-Agent")
    accept_language: str = Field(..., alias="Accept-Language")
    
    @field_validator('accept_language')
    @classmethod
    def validate_accept_language(cls, v: str) -> str:
        if not v:
            raise ValueError('Accept-Language не может быть пустым')
        
        parts = v.split(',')
        for part in parts:
            part = part.strip()
            if ';q=' in part:
                lang, quality = part.split(';q=')
                if not lang or not quality:
                    raise ValueError('Неверный формат Accept-Language')
                try:
                    q_value = float(quality)
                    if not (0 <= q_value <= 1):
                        raise ValueError('Значение q должно быть между 0 и 1')
                except ValueError:
                    raise ValueError('Неверный формат значения q')
            else:
                if not part:
                    raise ValueError('Неверный формат Accept-Language')
        
        return v
    
    class Config:
        populate_by_name = True