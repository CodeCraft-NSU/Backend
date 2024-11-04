"""
   CodeCraft PMS Backend Project

   파일명   : main.py                                                          
   생성자   : 김창환                                                        
                                                                              
   생성일   : 2024/10/14                                                       
   업데이트 : 2024/11/4                                                       
                                                                              
   설명     : FastAPI 서버 설정 및 계정, 프로젝트, 업무, 산출물 관리 라우터 포함                  
"""

# 모듈 추가 파트
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 라우터 추가 파트
from account import router as account_router
from project import router as project_router
from task import router as task_router
from output import router as output_router
from test import router as test_router # Frontend Axios에서 API 통신 테스트를 위한 라우터

# Database Project와의 연동을 위해 bashrc에 PYTHONPATH 정의 필요

app = FastAPI()

# CORSMiddleware 정의
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cd-api.chals.kim", "https://cd-web.chals.kim"], # API 서버의 접근을 허용할 도메인
    allow_credentials=True,
    allow_methods=["*"], # HTTP의 모든 Method 허용
    allow_headers=["*"], # 모든 헤더 허용
)

@app.get("/")
async def root():
    return {"message": "root of PMS Project API."}

app.include_router(account_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(output_router, prefix="/api")
app.include_router(test_router, prefix="/api") # 정식 Release 전 Delete 필요
