from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    # Simulated authentication for Authorized Cyber IO Credentials
    if not credentials.officerId.startswith("IO-"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Investigating Officer credentials ID"
        )
    
    return {
        "access_token": f"bearer_token_signed_for_{credentials.officerId}",
        "token_type": "bearer",
        "officerId": credentials.officerId
    }