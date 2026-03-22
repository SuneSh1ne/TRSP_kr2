from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from datetime import datetime, timezone
import uuid
from typing import Optional, Tuple, Dict


SECRET_KEY = "your-secret-key-1234567890"
serializer = URLSafeTimedSerializer(SECRET_KEY)

active_sessions: Dict[str, Dict] = {}

TEST_USERS = {
    "user123": {
        "password": "password123",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "username": "user123",
        "email": "user123@example.com"
    },
    "alice": {
        "password": "alice123",
        "user_id": "660e8400-e29b-41d4-a716-446655440001",
        "username": "alice",
        "email": "alice@example.com"
    }
}


def verify_user(username: str, password: str) -> Optional[Dict]:
    user = TEST_USERS.get(username)
    if user and user["password"] == password:
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"]
        }
    return None


def generate_user_id() -> str:
    return str(uuid.uuid4())


def create_session_token(user_id: str, timestamp: Optional[int] = None) -> str:
    if timestamp is None:
        timestamp = int(datetime.now(timezone.utc).timestamp())

    session_data = {
        "user_id": user_id,
        "timestamp": timestamp
    }
    
    signed_token = serializer.dumps(session_data)
    
    return signed_token


def parse_and_verify_session_token(token: str) -> Tuple[bool, Optional[str], Optional[int]]:
    try:
        session_data = serializer.loads(token, max_age=None)
        
        user_id = session_data.get("user_id")
        timestamp = session_data.get("timestamp")
        
        if user_id is None or timestamp is None:
            return False, None, None
        
        return True, user_id, timestamp
        
    except (BadSignature, SignatureExpired, ValueError, TypeError, Exception) as e:
        print(f"Token validation error: {e}")
        return False, None, None


def get_last_activity(user_id: str) -> Optional[int]:
    session = active_sessions.get(user_id)
    if session:
        return session.get("last_activity")
    return None


def update_last_activity(user_id: str, timestamp: int) -> None:
    if user_id in active_sessions:
        active_sessions[user_id]["last_activity"] = timestamp


def should_extend_session(last_activity: int, current_time: int) -> bool:
    time_diff = current_time - last_activity
    
    if time_diff >= 300:
        return None
    elif time_diff >= 180:
        return True
    else:
        return False

def create_user_session(user_id: str, user_data: Dict, current_time: int) -> None:
    active_sessions[user_id] = {
        "user_data": user_data,
        "last_activity": current_time
    }