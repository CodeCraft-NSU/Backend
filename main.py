from fastapi import FastAPI
from account import router as account_router
from project import router as project_router
import mysql_connection

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "root of PMS Project API."}

app.include_router(account_router, prefix="/api")
app.include_router(project_router, prefix="/api")