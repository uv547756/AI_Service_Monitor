from fastapi import FastAPI
from fastapi import APIRouter
from backend.app.api import machines, errors, health

app = FastAPI()

app.include_router(health.router)
app.include_router(machines.router, prefix="/api")
app.include_router(errors.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Backend is running"}
