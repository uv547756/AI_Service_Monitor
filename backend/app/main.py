from fastapi import FastAPI
from fastapi import APIRouter
app = FastAPI()
router = APIRouter()
@app.get("/")
async def root():
    return {"message": "Backend is running"}

