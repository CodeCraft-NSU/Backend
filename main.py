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
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException
from dotenv import load_dotenv
import os

# 라우터 추가 파트
from account import router as account_router
from project import router as project_router
from task import router as task_router
from output import router as output_router
from test import router as test_router  # Frontend Axios에서 API 통신 테스트를 위한 라우터

# Database Project와의 연동을 위해 각 Router에 sys.path 경로 정의 필요

app = FastAPI(debug=True)

# CORSMiddleware 정의
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cd-api.chals.kim", "https://cd-web.chals.kim"],  # API 서버의 접근을 허용할 도메인
    allow_credentials=True,
    allow_methods=["*"],  # HTTP의 모든 Method 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

load_dotenv()
API_KEY = os.getenv('API_KEY')

# 미들웨어 추가
class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Authorization 헤더에서 API Key 추출
        authorization = request.headers.get("Authorization")
        if authorization != API_KEY:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return await call_next(request)


# 미들웨어 등록
app.add_middleware(APIKeyMiddleware)


# 예외 핸들러
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    print(f"Unhandled error: {str(exc)}")  # 콘솔에 전체 예외 출력
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred", "error": str(exc)},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    print(f"HTTP error: {exc.detail}")  # 콘솔에 HTTP 예외 출력
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"Validation error: {exc.errors()}")  # 콘솔에 검증 오류 출력
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.get("/")
async def root():
    return {"message": "root of PMS Project API."}


# 라우터 추가
app.include_router(account_router, prefix="/api")
app.include_router(project_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(output_router, prefix="/api")
app.include_router(test_router, prefix="/api")  # 정식 Release 전 Delete 필요
