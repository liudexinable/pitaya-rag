from pathlib import Path

from fastapi import APIRouter, Request
from flask import render_template
from starlette.templating import Jinja2Templates

router = APIRouter(
    prefix="/update",
    tags=["update"]
)

base_dir = Path(__file__).parent.parent.parent
templates = Jinja2Templates(directory=str(base_dir / "templates"))
templates.env.variable_start_string = "[["
templates.env.variable_end_string = ']]'

@router.get('/index')
async def chat(request: Request):
    print(templates.get_template("update.html"))
    return templates.TemplateResponse("update.html", {"request": request})