# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    health_router,
    auth_router,
    school_histories_router,
    matching_router,
    communities_router,
)
from app.core.config import settings  # 향후 확장용


def create_app() -> FastAPI:
    app = FastAPI(
        title="Intersection API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(school_histories_router)
    app.include_router(matching_router)
    app.include_router(communities_router)

    return app


app = create_app()
