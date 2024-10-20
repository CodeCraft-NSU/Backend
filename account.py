# 계정/세션 관련 기능
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import mysql_connection  # MySQL 연결 기능 수행

router = APIRouter()

class SignUp_Payload(BaseModel):
    is_student: bool
    name: str
    univ_id: int
    email: str
    id: str
    pw: str
    department: int

class Signin_Payload(BaseModel):
    id: str
    pw: str

@router.get("/acc_signup")
async def api_acc_signup_get():
    return {"Message": "Please use POST method for signup."}

@router.post("/acc_signup")
async def api_acc_signup_post(payload: SignUp_Payload):
    """
    DB에 사용자 정보를 삽입하는 쿼리 실행
    예시로, 가상의 함수 insert_user()를 사용한다고 가정
    """
    try:
        # 예시: 사용자 정보 데이터베이스에 삽입
        insert_result = insert_user(payload)  # insert_user 함수는 payload의 정보를 DB에 삽입
        return {"Result": insert_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/acc_signin")
async def api_acc_signin_get():
    return {"Message": "Please use POST method for signin."}

@router.post("/acc_signin")
async def api_acc_signin_post(payload: Signin_Payload):
    """
    MySQL과 연동하여 계정 확인 후 로그인 성공 여부 확인
    예시로, 가상의 함수 validate_user()를 사용한다고 가정
    """
    try:
        # 사용자 유효성 검사
        is_valid_user = validate_user(payload.id, payload.pw)  # validate_user 함수는 ID와 PW를 체크
        
        if is_valid_user:
            token = generate_token(payload.id)  # 가상의 토큰 생성 함수
            return {"login": "True", "Token": token}
        else:
            return JSONResponse(status_code=401, content={"login": "failed"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
