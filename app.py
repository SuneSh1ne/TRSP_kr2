from fastapi import FastAPI, HTTPException, Request, Response, Depends, Header, status
from datetime import datetime, timezone
from typing import Optional

from models import UserCreate, LoginRequest, CommonHeaders
from products import get_product_by_id, search_products
from auth import (
    verify_user, create_session_token, parse_and_verify_session_token,
    create_user_session, update_last_activity, should_extend_session,
    active_sessions, TEST_USERS
)

app = FastAPI(
    title="FastAPI Server Application",
    description="Контрольная работа №2 по технологиям разработки серверных приложений",
    version="1.0.0"
)


@app.post(
    "/create_user",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Пользователь успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Alice",
                        "email": "alice@example.com",
                        "age": 30,
                        "is_subscribed": True
                    }
                }
            }
        },
        400: {
            "description": "Ошибка валидации данных",
            "content": {
                "application/json": {
                    "example": {
                        "code": 400,
                        "status": "error",
                        "message": "Ошибка валидации входных данных",
                        "errors": [
                            {
                                "field": "email",
                                "message": "value is not a valid email address",
                                "type": "value_error"
                            },
                            {
                                "field": "age",
                                "message": "ensure this value is greater than or equal to 1",
                                "type": "value_error"
                            }
                        ],
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        422: {
            "description": "Необрабатываемая сущность - неверный формат JSON",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "status": "error",
                        "message": "Неверный формат JSON",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        429: {
            "description": "Слишком много запросов",
            "content": {
                "application/json": {
                    "example": {
                        "code": 429,
                        "status": "error",
                        "message": "Превышен лимит запросов. Попробуйте позже",
                        "retry_after": 60,
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "code": 500,
                        "status": "error",
                        "message": "Внутренняя ошибка сервера",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        }
    }
)
async def create_user(user: UserCreate):
    return user


@app.get(
    "/product/{product_id}",
    responses={
        200: {
            "description": "Продукт успешно найден",
            "content": {
                "application/json": {
                    "example": {
                        "product_id": 123,
                        "name": "Smartphone",
                        "category": "Electronics",
                        "price": 599.99
                    }
                }
            }
        },
        400: {
            "description": "Неверный ID продукта",
            "content": {
                "application/json": {
                    "example": {
                        "code": 400,
                        "status": "error",
                        "message": "ID продукта должен быть положительным целым числом",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        404: {
            "description": "Продукт не найден",
            "content": {
                "application/json": {
                    "example": {
                        "code": 404,
                        "status": "error",
                        "message": "Продукт с ID 999 не найден",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "code": 500,
                        "status": "error",
                        "message": "Внутренняя ошибка сервера",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        }
    }
)
async def get_product(product_id: int):
    product = get_product_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get(
    "/products/search",
    responses={
        200: {
            "description": "Поиск выполнен успешно",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "product_id": 123,
                            "name": "Smartphone",
                            "category": "Electronics",
                            "price": 599.99
                        },
                        {
                            "product_id": 789,
                            "name": "Iphone",
                            "category": "Electronics",
                            "price": 1299.99
                        }
                    ]
                }
            }
        },
        400: {
            "description": "Ошибка в параметрах запроса",
            "content": {
                "application/json": {
                    "example": {
                        "code": 400,
                        "status": "error",
                        "message": "Параметр 'keyword' обязателен для заполнения",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        422: {
            "description": "Неверный формат параметров",
            "content": {
                "application/json": {
                    "example": {
                        "code": 422,
                        "status": "error",
                        "message": "Параметр 'limit' должен быть целым числом от 1 до 100",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "code": 500,
                        "status": "error",
                        "message": "Внутренняя ошибка сервера",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        }
    }
)
async def products_search(
    keyword: str,
    category: Optional[str] = None,
    limit: int = 10
):
    if limit <= 0 or limit > 100:
        limit = 10
    
    results = search_products(keyword, category, limit)
    return results


@app.post(
    "/login",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Успешная аутентификация",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Login successful",
                        "user": {
                            "user_id": "550e8400-e29b-41d4-a716-446655440000",
                            "username": "user123",
                            "email": "user123@example.com"
                        }
                    }
                }
            },
            "headers": {
                "Set-Cookie": {
                    "description": "Установка session_token cookie",
                    "example": "session_token=abc123...; HttpOnly; Max-Age=300"
                }
            }
        },
        400: {
            "description": "Неверный формат запроса",
            "content": {
                "application/json": {
                    "example": {
                        "code": 400,
                        "status": "error",
                        "message": "Неверный формат JSON",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        401: {
            "description": "Ошибка аутентификации",
            "content": {
                "application/json": {
                    "example": {
                        "code": 401,
                        "status": "error",
                        "message": "Неверное имя пользователя или пароль",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        429: {
            "description": "Слишком много попыток входа",
            "content": {
                "application/json": {
                    "example": {
                        "code": 429,
                        "status": "error",
                        "message": "Слишком много попыток входа. Подождите 5 минут",
                        "retry_after": 300,
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "code": 500,
                        "status": "error",
                        "message": "Внутренняя ошибка сервера",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        }
    }
)
async def login(request: LoginRequest, response: Response):
    user = verify_user(request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    user_id = user["user_id"]
    current_time = int(datetime.now(timezone.utc).timestamp())
    
    session_token = create_session_token(user_id, current_time)

    create_user_session(user_id, user, current_time)

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,
        max_age=300,
        samesite="lax"
    )

    return {"message": "Login successful", "user": user}


@app.get(
    "/profile",
    responses={
        200: {
            "description": "Профиль успешно получен",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "550e8400-e29b-41d4-a716-446655440000",
                        "username": "user123",
                        "email": "user123@example.com",
                        "last_activity": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        401: {
            "description": "Не авторизован",
            "content": {
                "application/json": {
                    "examples": {
                        "no_token": {
                            "summary": "Отсутствует токен сессии",
                            "value": {
                                "code": 401,
                                "status": "error",
                                "message": "Unauthorized - No session token",
                                "timestamp": "2025-04-10T10:30:00+00:00"
                            }
                        },
                        "invalid_token": {
                            "summary": "Неверный токен",
                            "value": {
                                "code": 401,
                                "status": "error",
                                "message": "Invalid session - Bad signature",
                                "timestamp": "2025-04-10T10:30:00+00:00"
                            }
                        },
                        "expired": {
                            "summary": "Сессия истекла",
                            "value": {
                                "code": 401,
                                "status": "error",
                                "message": "Session expired - Inactive for more than 5 minutes",
                                "timestamp": "2025-04-10T10:30:00+00:00"
                            }
                        }
                    }
                }
            }
        },
        403: {
            "description": "Доступ запрещен",
            "content": {
                "application/json": {
                    "example": {
                        "code": 403,
                        "status": "error",
                        "message": "Access denied - Insufficient permissions",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "code": 500,
                        "status": "error",
                        "message": "Внутренняя ошибка сервера",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        }
    }
)
@app.get("/user")
async def get_profile(request: Request, response: Response):
    session_token = request.cookies.get("session_token")

    if not session_token:
        response.status_code = 401
        return {"message": "Unauthorized"}

    is_valid, user_id, token_timestamp = parse_and_verify_session_token(session_token)
    
    if not is_valid or user_id is None:
        response.status_code = 401
        return {"message": "Invalid session"}
    
    session_data = active_sessions.get(user_id)
    if not session_data:
        response.status_code = 401
        return {"message": "Session expired"}
    
    current_time = int(datetime.now(timezone.utc).timestamp())
    last_activity = session_data.get("last_activity", token_timestamp)
    
    extend_needed = should_extend_session(last_activity, current_time)
    
    if extend_needed is None:
        active_sessions.pop(user_id, None)
        response.status_code = 401
        return {"message": "Session expired"}
    
    if extend_needed:
        new_timestamp = current_time
        new_token = create_session_token(user_id, new_timestamp)
        
        response.set_cookie(
            key="session_token",
            value=new_token,
            httponly=True,
            secure=False,
            max_age=300,
            samesite="lax"
        )
        
        update_last_activity(user_id, current_time)
    
    user_data = session_data.get("user_data", {})
    return {
        "user_id": user_id,
        "username": user_data.get("username"),
        "email": user_data.get("email"),
        "last_activity": datetime.fromtimestamp(last_activity, timezone.utc).isoformat()
    }


@app.get(
    "/headers",
    responses={
        200: {
            "description": "Заголовки успешно получены",
            "content": {
                "application/json": {
                    "example": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Accept-Language": "en-US,en;q=0.9,es;q=0.8"
                    }
                }
            }
        },
        400: {
            "description": "Ошибка валидации заголовков",
            "content": {
                "application/json": {
                    "example": {
                        "code": 400,
                        "status": "error",
                        "message": "Ошибка валидации заголовков",
                        "errors": [
                            {
                                "field": "Accept-Language",
                                "message": "Неверный формат Accept-Language",
                                "type": "value_error"
                            }
                        ],
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        406: {
            "description": "Неподдерживаемый формат",
            "content": {
                "application/json": {
                    "example": {
                        "code": 406,
                        "status": "error",
                        "message": "Неподдерживаемый Accept header",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "code": 500,
                        "status": "error",
                        "message": "Внутренняя ошибка сервера",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        }
    }
)
async def get_headers(headers: CommonHeaders = Depends()):
    return {
        "User-Agent": headers.user_agent,
        "Accept-Language": headers.accept_language
    }


@app.get(
    "/info",
    responses={
        200: {
            "description": "Информация успешно получена",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
                        "headers": {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                            "Accept-Language": "en-US,en;q=0.9,es;q=0.8"
                        }
                    }
                }
            },
            "headers": {
                "X-Server-Time": {
                    "description": "Текущее время сервера",
                    "example": "2025-04-10T10:30:00+00:00"
                }
            }
        },
        400: {
            "description": "Ошибка валидации заголовков",
            "content": {
                "application/json": {
                    "example": {
                        "code": 400,
                        "status": "error",
                        "message": "Ошибка валидации заголовков",
                        "errors": [
                            {
                                "field": "Accept-Language",
                                "message": "Неверный формат Accept-Language",
                                "type": "value_error"
                            }
                        ],
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {
                        "code": 500,
                        "status": "error",
                        "message": "Внутренняя ошибка сервера",
                        "timestamp": "2025-04-10T10:30:00+00:00"
                    }
                }
            }
        }
    }
)
async def get_info(
    headers: CommonHeaders = Depends(),
    response: Response = None
):
    server_time = datetime.now(timezone.utc).isoformat()
    response.headers["X-Server-Time"] = server_time
    
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": headers.user_agent,
            "Accept-Language": headers.accept_language
        }
    }