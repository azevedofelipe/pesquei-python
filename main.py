from fastapi import FastAPI

from routers.catches import router as catches_router

app = FastAPI()

app.include_router(catches_router)