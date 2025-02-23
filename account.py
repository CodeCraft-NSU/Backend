"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : account.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/10/16                                                      
   업데이트 : 2025/02/15          
                                                                             
   설명     : 계정 생성, 로그인, 세션 관리를 위한 API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from logger import logger
import sys, os, random, string, logging

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

# class Usrpm_Payload(BaseModel): 미사용 비활성화 (25.02.11)
#     token: str

class Checksession_Payload(BaseModel):
    user_id: str
    token: str

class AccCheck_Payload(BaseModel):
    univ_id: int
    name: str
    email: str
    user_id: str

class PwReset_Payload(BaseModel):
    univ_id: int
    pw: str

class FineName_Payload(BaseModel):
    univ_id: int

class FindProf_Payload(BaseModel):
    department: int

def generate_token():
    """랜덤한 15자리 토큰 생성"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=15))


@router.post("/acc/checksession")
async def check_session(payload: Checksession_Payload):
    """세션 유효성 확인"""
    try:
        is_valid = account_DB.validate_user_token(payload.user_id, payload.token)
        if isinstance(is_valid, Exception):
            raise HTTPException(status_code=401, detail=f"Invalid session: {str(is_valid)}")
        if is_valid:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Session valid"}
        raise HTTPException(status_code=401, detail="Invalid session token")
    except Exception as e:
        logger.debug(f"Error validating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error validating session: {str(e)}")


@router.post("/acc/signup")
async def api_acc_signup_post(payload: SignUp_Payload):
    """사용자 가입"""
    try:
        token = generate_token()
        result = account_DB.insert_user(payload, token)
        if result is True:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Signup successful", "PAYLOADS": {"Token": token}}
        elif isinstance(result, tuple) and result[0] == 1062:
            return {"RESULT_CODE": 409, "RESULT_MSG": "Duplicate entry: This univ_id is already registered"}
        else:
            # print(result)
            raise HTTPException(status_code=500, detail=f"Error during signup: {str(result)}")
    except Exception as e:
        if "1062" in str(e):
            return {"RESULT_CODE": 409, "RESULT_MSG": "Duplicate entry: This univ_id is already registered"}
        else:
            raise HTTPException(status_code=500, detail=f"Unhandled exception during signup: {str(e)}")

@router.post("/acc/signin")
async def api_acc_signin_post(payload: Signin_Payload):
    """사용자 로그인"""
    try:
        s_no = account_DB.validate_user(payload.id, payload.pw)
        if s_no is None:  # 로그인 실패 처리
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if isinstance(s_no, Exception):  # 예외 발생 처리
            raise HTTPException(status_code=500, detail=f"Internal error during validation: {str(s_no)}")
        token = generate_token()
        save_result = account_DB.save_signin_user_token(payload.id, token)
        if isinstance(save_result, Exception):  # 토큰 저장 중 오류 처리
            raise HTTPException(status_code=500, detail=f"Error saving session token: {str(save_result)}")
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Login successful",
            "PAYLOADS": {
                "Token": token,
                "Univ_ID": s_no
            }
        }
    except HTTPException as http_err:
        # 명시적으로 처리된 HTTP 예외는 재사용
        raise http_err
    except Exception as e:
        # 기타 모든 예외는 500으로 처리
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

@router.post("/acc/checkacc")
async def api_acc_check(payload: AccCheck_Payload):
    """
    비밀번호 리셋 전 정보 확인 함수
    비밀번호 찾기 기능의 경우, 먼저 이 엔드포인트를 통해 Return 값이 200인지 확인 후,
    맞다면 api_acc_pwreset 함수 실행
    """
    try:
        result = account_DB.find_user_pw(
            univ_id = payload.univ_id,
            name = payload.name,
            email = payload.email,
            id = payload.user_id
        )
        if result is True:
            return {"RESULT_CODE": 200, "RESULT_MSG": "OK"}
        else:
            # raise HTTPException(status_code=500, detail="Account validation failed")
            return {"RESULT_CODE": 400, "RESULT_MSG": "Account validation failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unhandled exception during account validation: {str(e)}")

@router.post("/acc/resetpw")
async def api_acc_pwreset(payload: PwReset_Payload):
    """비밀번호 리셋(변경) 함수"""
    try:
        result = account_DB.edit_user_pw(
            payload.univ_id,
            payload.pw
        )
        if result is True:
            return {"RESULT_CODE": 200, "RESULT_MSG": "OK"}
        else:
            # raise HTTPException(status_code=500, detail="Password update failed")
            return {"RESULT_CODE": 400, "RESULT_MSG": "Password update failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unhandled exception while updating password: {str(e)}")

@router.post("/acc/find_sname")
async def api_acc_find_student_name(payload: FineName_Payload):
    """학번으로 학생 이름을 찾는 기능"""
    try:
        result = account_DB.fetch_student_name(payload.univ_id)
        if isinstance(result, Exception) or result == None:
            raise HTTPException(status_code=500, detail=f"Error in find student name Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Find Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in find student name Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in find student name Operation: {str(e)}")

# @router.post("/acc/find_prof") # 미사용 주석처리 (25.02.15)
# async def api_acc_find_professor(payload: FindProf_Payload):
#     """자신의 학과에 속한 교수 리스트를 불러오는 기능"""
#     return