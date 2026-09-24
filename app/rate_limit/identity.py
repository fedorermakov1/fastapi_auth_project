from fastapi import Request
from app.models import User

def get_ip_client_id(request: Request) -> str:
    return f"ip:{request.client.host}"

def get_user_client_id(
    request: Request,
    current_user: User
) -> str:
    return (
        f"user:{current_user.id}:"
        f"{request.url.path}"
    )