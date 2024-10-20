from fastapi import FastAPI
from account import router as account_router
from project import router as project_router
from task import router as task_router
from output import router as output_router

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "root of PMS Project API."}

app.include_router(account_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(output_router, prefix="/api")