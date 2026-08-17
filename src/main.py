import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
for _p in (str(_SRC), str(_REPO)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import api_router
from src.api.routes import base_router, health_router, chat_router

FRONTEND_DIR = _REPO / "frontend"

app = FastAPI(
    title="ShopWise Agent API",
    version="v1",
    description="Backend API for the ShopWise Agent",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(base_router)
app.include_router(health_router)
app.include_router(chat_router)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse(str(FRONTEND_DIR / "index.html"))
