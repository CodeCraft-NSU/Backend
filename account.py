from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys, os
import random
import string

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
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

class Usrpm_Payload(BaseModel):
    token: str

def generate_token():
    """랜덤한 15자리 토큰 생성"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=15))

@router.post("/acc/checksession")
async def check_session(user_id: str, token: str):
    """세션 유효성 확인"""
    try:
        is_valid = account_DB.validate_user_token(user_id, token)
        if is_valid:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Session valid"}
        else:
            raise HTTPException(status_code=401, detail="Invalid session token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating session: {str(e)}")

@router.post("/acc/signup")
async def api_acc_signup_post(payload: SignUp_Payload):
    """사용자 가입"""
    try:
        token = generate_token()
        result = account_DB.insert_user(payload, token)
        if result is True:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Signup successful", "PAYLOADS": {"Token": token}}
        else:
            print(result)
            raise HTTPException(status_code=500, detail=f"Error during signup: {str(result)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unhandled exception during signup: {str(e)}")

@router.post("/acc/signin")
async def api_acc_signin_post(payload: Signin_Payload):
    """사용자 로그인"""
    try:
        is_valid = account_DB.validate_user(payload.id, payload.pw)
        if isinstance(is_valid, Exception):
            raise HTTPException(status_code=500, detail=f"Error during validation: {str(is_valid)}")
        if is_valid:
            token = generate_token()
            save_result = account_DB.save_signin_user_token(payload.id, token)
            if isinstance(save_result, Exception):
                raise HTTPException(status_code=500, detail=f"Error saving session token: {str(save_result)}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Login successful", "PAYLOADS": {"Token": token}}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unhandled exception during login: {str(e)}")

@router.post("/acc/signout")
async def api_acc_signout_post(payload: SignOut_Payload):
    """사용자 로그아웃"""
    try:
        result = account_DB.signout_user(payload.token)
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error during logout: {str(result)}")
        if result is True:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Logout successful"}
        else:
            raise HTTPException(status_code=500, detail="Logout failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unhandled exception during logout: {str(e)}")

@router.post("/acc/delacc")
async def api_acc_delacc_post(payload: DelAcc_Payload):
    """계정 삭제"""
    try:
        result = account_DB.delete_user(payload.id)
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error during account deletion: {str(result)}")
        if result is True:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Account deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Account deletion failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unhandled exception during account deletion: {str(e)}")

@router.post("/acc/usrpm")
async def api_acc_userpm_post(payload: Usrpm_Payload):
    """사용자 권한 확인 (구체적 구현 필요)"""
    # 권한 확인 로직이 DB와 연동되지 않았으므로 예제 응답 반환
    return {"RESULT_CODE": 200, "RESULT_MSG": "User permission fetched successfully", "PAYLOADS": {}}
