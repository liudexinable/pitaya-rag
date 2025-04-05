from pathlib import Path

from fastapi import APIRouter, Request
from flask import render_template
from starlette.templating import Jinja2Templates

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

base_dir = Path(__file__).parent.parent.parent
templates = Jinja2Templates(directory=str(base_dir / "templates"))

@router.get('/index')
async def chat(request: Request):
    print(templates.get_template("chat.html"))
    return templates.TemplateResponse("chat.html", {"request": request})