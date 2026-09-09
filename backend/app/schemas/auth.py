from pydantic import BaseModel

class LoginRequest(BaseModel):
    officerId: str
    pin: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    officerId: str