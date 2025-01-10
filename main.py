"""
   CodeCraft PMS Backend Project

   파일명   : main.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2024/10/14                                                       
   업데이트 : 2024/11/24                                                       
                                                                              
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
from grade import router as grade_router
from wbs import router as wbs_router
from llm import router as llm_router
from docs_converter import router as docs_router
from test import router as test_router  # Frontend Axios에서 API 통신 테스트를 위한 라우터

# Database Project와의 연동을 위해 각 Router에 sys.path 경로 정의 필요
app = FastAPI(debug=True)

load_dotenv()
API_KEY = os.getenv('API_KEY')
# print(f"Loaded API_KEY: {API_KEY}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cd-web.chals.kim"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization"],  # Authorization 헤더 명시적으로 허용
)

# API KEY 인증 비활성화 (24.11.24)
# class APIKeyMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         if request.method == "OPTIONS":
#             return Response(status_code=200, headers={
#                 "Access-Control-Allow-Origin": request.headers.get("Origin", "*"),
#                 "Access-Control-Allow-Methods": "*",
#                 "Access-Control-Allow-Headers": "*",
#             })
#         authorization = request.headers.get("Authorization")
#         # print(f"Authorization Header: {authorization}")
#         # print(f"Headers: {request.headers}")  # 전체 헤더 출력
#         if authorization != API_KEY:
#             raise HTTPException(status_code=401, detail="Unauthorized")
#         return await call_next(request)

# # 미들웨어 등록
# app.add_middleware(APIKeyMiddleware)


# 예외 핸들러
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    print(f"Unhandled error: {str(exc)}")  # 콘솔에 전체 예외 출력
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred", "error": str(exc)},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
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
app.include_router(grade_router, prefix="/api")
app.include_router(wbs_router, prefix="/api")
app.include_router(llm_router, prefix="/api")
app.include_router(docs_router, prefix="/api")
app.include_router(test_router, prefix="/api")  # 정식 Release 전 Delete 필요
