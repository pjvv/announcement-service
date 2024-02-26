from fastapi import FastAPI
from logging_config import configure_logging
from routes import router as announcement_router

configure_logging()

app = FastAPI()

app.include_router(announcement_router)
