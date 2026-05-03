from fastapi import FastAPI

from .api.routes import analysis, detections, health
from .core.config import settings
from .db import init_db


def create_app() -> FastAPI:
    init_db()
    application = FastAPI(title=settings.app_name)
    application.include_router(health.router)
    application.include_router(analysis.router)
    application.include_router(detections.router)
    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
