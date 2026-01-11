from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.database import get_session
from app.auth import get_current_user_from_session, require_auth
from app.models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, session: Session = Depends(get_session)):
    """Home page - redirect to dashboard if authenticated, otherwise show auth page"""
    user = get_current_user_from_session(request, session)
    
    if user:
        return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
    else:
        return templates.TemplateResponse("auth.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, session: Session = Depends(get_session)):
    """Dashboard page - requires authentication"""
    user = require_auth(request, session)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
