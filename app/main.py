import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.api import knowledge_api
from app.routes.web_ui import chat_web, update_web

app = FastAPI()

app.include_router(chat_web.router)
app.include_router(update_web.router)
app.include_router(knowledge_api.router)

# 挂载静态文件（确保目录路径正确）
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


