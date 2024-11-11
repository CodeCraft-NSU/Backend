"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : account.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/10/16                                                      
   업데이트 : 2024/11/11                                                     
                                                                             
   설명     : 계정 생성, 로그인, 세션 관리를 위한 API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys, os

sys.path.append(os.path.abspath('/data/Database Project')) # Database Project와 연동하기 위해 사용
import account_DB

router = APIRouter()

class SignUp_Payload(BaseModel):
    name: str
    univ_id: int
    email: str
    id: str
    pw: str
    department: int

class Signin_Payload(BaseModel):
    id: str
    pw: str

class SignOut_Payload(BaseModel):
    token: str

class DelAcc_Payload(BaseModel):
    id: str

def generate_token():
    """
    알파벳 대소문자, 숫자, 특수문자를 섞어 15자 길이의 랜덤 토큰 생성
    """
    # 사용할 문자 목록: 알파벳 대소문자, 숫자, 특수문자
    characters = string.ascii_letters + string.digits + string.punctuation
    # 15자리 랜덤 문자열 생성
    token = ''.join(random.choices(characters, k=15))
    return token

def check_session(user_id: str, token: str):
    # validate_user_token 함수를 호출하여 토큰 유효성 확인
    if not account_DB.validate_user_token(user_id, token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return True

@router.post("/acc/signup")
async def api_acc_signup_post(payload: SignUp_Payload):
    """
    DB에 사용자 정보를 삽입하는 쿼리 실행
    Database Project의 account_DB에 정의돼있는 insert_user 함수 사용
    """
    Token = generate_token() # Session 토큰 생성
    insert_result = account_DB.insert_user(payload, Token)  # insert_user 함수는 payload의 정보를 DB에 삽입
    if insert_result is True:
        return {"RESULT_CODE": 200,
                "RESULT_MSG": "Success",
                "PAYLOADS": {
                                "Token": Token
                            }}
    else:
        raise HTTPException(status_code=500, detail={"RESULT_CODE": 500,
                                                        "RESULT_MSG": "Internal Server Error",
                                                        "PAYLOADS": {}})

@router.post("/acc/signin")
async def api_acc_signin_post(payload: Signin_Payload):
    """
    MySQL과 연동하여 계정 확인 후 로그인 성공 여부 확인
    Database Project의 account_DB에 정의돼있는 validate_user 함수 사용
    """
    try:
        # 사용자 유효성 검사
        is_valid_user = account_DB.validate_user(payload.id, payload.pw)  # validate_user 함수는 ID와 PW를 체크
        
        if is_valid_user:
            Token = generate_token()  # 'Token' 변수 생성
            return {"RESULT_CODE": 200,
                    "RESULT_MSG": "Success",
                    "PAYLOADS": {
                                    "Token": Token
                                }}
        else:
            return JSONResponse(status_code=401, content={"RESULT_CODE": 401,
                                                          "RESULT_MSG": "Unauthorized",
                                                          "PAYLOADS": {}})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"RESULT_CODE": 500,
                                                     "RESULT_MSG": "Internal Server Error",
                                                     "PAYLOADS": {}})

@router.post("/acc/signout")
async def api_acc_signout_post(payload: SignOut_Payload):
    """
    로그아웃 기능을 구현함
    token 값을 payload로 받아 session을 폐기함
    """
    return {}

@router.post("/acc/delacc")
async def api_acc_delacc_post(payload: DelAcc_Payload):
    """
    계정 삭제 기능을 구현함
    """
    if account_DB.delete_user(payload.id):
        return {"RESULT_CODE": 200,
                "RESULT_MSG": "Success",
                "PAYLOADS": {}}
    else:
        return {"RESULT_CODE": 500,
                "RESULT_MSG": "Internal Server Error",
                "PAYLOADS": {}}