from fastapi import FastAPI

from .api.routes import analysis, detections, health
from .core.config import settings
from .db import init_db


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_name)
    application.include_router(health.router)
    application.include_router(analysis.router)
    application.include_router(detections.router)

    @application.on_event("startup")
    def on_startup() -> None:
        init_db()

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port)
