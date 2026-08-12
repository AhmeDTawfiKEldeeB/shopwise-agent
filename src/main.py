from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import api_router
from src.api.routes import base_router, health_router


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