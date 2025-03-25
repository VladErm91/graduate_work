import logging
from urllib.parse import urlencode

from core.config import settings
from core.jwt import create_access_token, verify_token
from db.db import get_session
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm


logger = logging.getLogger(__name__)
router = APIRouter()


