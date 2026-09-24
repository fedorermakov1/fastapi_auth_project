from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenData(BaseModel):
    user_id: int | None = None

class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str