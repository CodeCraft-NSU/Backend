"""                                                          
   CodeCraft PMS Backend Project

   파일명   : main.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/10/14                                                       
   업데이트 : 2024/10/20                                                      
                                                                             
   설명     : FastAPI 서버 설정 및 계정, 프로젝트, 업무, 산출물 관리 라우터 포함                   
"""

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