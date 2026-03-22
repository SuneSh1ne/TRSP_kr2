from fastapi import FastAPI, HTTPException, Request, Response, Depends, Header
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

@app.post("/create_user")
async def create_user(user: UserCreate):
    return user

@app.get("/product/{product_id}")
async def get_product(product_id: int):
    product = get_product_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/products/search")
async def products_search(
    keyword: str,
    category: Optional[str] = None,
    limit: int = 10
):
    if limit <= 0 or limit > 100:
        limit = 10
    
    results = search_products(keyword, category, limit)
    return results

@app.post("/login")
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

@app.get("/profile")
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

@app.get("/headers")
async def get_headers(headers: CommonHeaders = Depends()):
    return {
        "User-Agent": headers.user_agent,
        "Accept-Language": headers.accept_language
    }

@app.get("/info")
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