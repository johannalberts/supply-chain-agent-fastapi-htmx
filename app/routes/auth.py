from fastapi import APIRouter, Request, Response, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlmodel import Session
from app.database import get_session
from app.auth import authenticate_user, create_user, create_access_token, get_current_user_from_session
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    """Handle user login"""
    user = authenticate_user(session, username, password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create access token
    access_token = create_access_token(data={"user_id": user.id, "username": user.username})
    
    # Set cookie
    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie(
        key=settings.session_cookie_name,
        value=access_token,
        max_age=settings.session_max_age,
        httponly=True,
        samesite="lax"
    )
    
    return response


@router.post("/signup")
async def signup(
    request: Request,
    response: Response,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    """Handle user signup"""
    try:
        user = create_user(session, username, email, password)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Create access token
    access_token = create_access_token(data={"user_id": user.id, "username": user.username})
    
    # Set cookie
    response = JSONResponse(content={"message": "Account created successfully"})
    response.set_cookie(
        key=settings.session_cookie_name,
        value=access_token,
        max_age=settings.session_max_age,
        httponly=True,
        samesite="lax"
    )
    
    return response


@router.post("/logout")
async def logout(response: Response):
    """Handle user logout"""
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key=settings.session_cookie_name)
    return response
