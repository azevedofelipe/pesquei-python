from fastapi import FastAPI

from routers.auth import router as auth_router
from routers.catches import router as catches_router
from routers.lures import router as lures_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(catches_router)
app.include_router(lures_router)