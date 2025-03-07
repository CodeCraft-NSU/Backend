"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : account.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/10/16                                                      
   업데이트 : 2025/02/24
                                                                             
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

class LoadProfPayload(BaseModel):
    subj_no: int


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
            logger.error(f"Invalid session for user {payload.user_id}: {str(is_valid)}", exc_info=True)
            raise HTTPException(status_code=401, detail=f"Invalid session: {str(is_valid)}")
        if is_valid:
            logger.info(f"Session valid for user {payload.user_id}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Session valid"}
        logger.warning(f"Invalid session token for user {payload.user_id}")
        raise HTTPException(status_code=401, detail="Invalid session token")
    except Exception as e:
        logger.error(f"Unexpected error validating session for user {payload.user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error validating session: {str(e)}")


@router.post("/acc/signup")
async def api_acc_signup_post(payload: SignUp_Payload):
    """사용자 가입"""
    try:
        token = generate_token()
        result = account_DB.insert_user(payload, token)
        if result is True:
            logger.info(f"User {payload.univ_id} signed up successfully")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Signup successful", "PAYLOADS": {"Token": token}}
        if isinstance(result, tuple) and result[0] == 1062:
            logger.warning(f"Duplicate signup attempt: {payload.univ_id} is already registered")
            return {"RESULT_CODE": 409, "RESULT_MSG": "Duplicate entry: This univ_id is already registered"}
        logger.error(f"Unexpected signup error: {str(result)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during signup: {str(result)}")
    except Exception as e:
        logger.error(f"Unhandled exception during signup: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unhandled exception during signup: {str(e)}")


@router.post("/acc/signin")
async def api_acc_signin_post(payload: Signin_Payload):
    """사용자 로그인"""
    try:
        s_no = account_DB.validate_user(payload.id, payload.pw)
        if s_no is None:
            logger.warning(f"Invalid login attempt: {payload.id}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if isinstance(s_no, Exception):
            logger.error(f"Internal error during validation: {str(s_no)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal error during validation: {str(s_no)}")
        token = generate_token()
        save_result = account_DB.save_signin_user_token(payload.id, token)
        if isinstance(save_result, Exception):
            logger.error(f"Error saving session token for user {payload.id}: {str(save_result)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error saving session token: {str(save_result)}")
        logger.info(f"User {payload.id} signed in successfully")
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Login successful",
            "PAYLOADS": {
                "Token": token,
                "Univ_ID": s_no
            }
        }
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"Unhandled exception during login for user {payload.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unhandled exception during login: {str(e)}")

@router.post("/acc/signout")
async def api_acc_signout_post(payload: SignOut_Payload):
    """사용자 로그아웃"""
    try:
        result = account_DB.signout_user(payload.token)
        if isinstance(result, Exception):
            logger.error(f"Error during logout: {str(result)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error during logout: {str(result)}")
        if result is True:
            logger.info("User logged out successfully")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Logout successful"}
        logger.warning("Logout failed")
        raise HTTPException(status_code=500, detail="Logout failed")
    except Exception as e:
        logger.error(f"Unhandled exception during logout: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unhandled exception during logout: {str(e)}")

@router.post("/acc/delacc")
async def api_acc_delacc_post(payload: DelAcc_Payload):
    """계정 삭제"""
    try:
        result = account_DB.delete_user(payload.id)
        if isinstance(result, Exception):
            logger.error(f"Error during account deletion: {str(result)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error during account deletion: {str(result)}")
        if result is True:
            logger.info(f"Account {payload.id} deleted successfully")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Account deleted successfully"}
        logger.warning(f"Account deletion failed for {payload.id}")
        raise HTTPException(status_code=500, detail="Account deletion failed")
    except Exception as e:
        logger.error(f"Unhandled exception during account deletion: {str(e)}", exc_info=True)
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
            univ_id=payload.univ_id,
            name=payload.name,
            email=payload.email,
            id=payload.user_id
        )
        if result is True:
            logger.info(f"Account validation successful for user {payload.user_id}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "OK"}
        logger.warning(f"Account validation failed for user {payload.user_id}")
        return {"RESULT_CODE": 400, "RESULT_MSG": "Account validation failed"}
    except Exception as e:
        logger.error(f"Unhandled exception during account validation for user {payload.user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unhandled exception during account validation: {str(e)}")

@router.post("/acc/resetpw")
async def api_acc_pwreset(payload: PwReset_Payload):
    """비밀번호 리셋(변경) 함수"""
    try:
        result = account_DB.edit_user_pw(payload.univ_id, payload.pw)
        if result is True:
            logger.info(f"Password reset successful for user {payload.univ_id}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "OK"}
        logger.warning(f"Password update failed for user {payload.univ_id}")
        return {"RESULT_CODE": 400, "RESULT_MSG": "Password update failed"}
    except Exception as e:
        logger.error(f"Unhandled exception while updating password for user {payload.univ_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unhandled exception while updating password: {str(e)}")

@router.post("/acc/find_sname")
async def api_acc_find_student_name(payload: FineName_Payload):
    """학번으로 학생 이름을 찾는 기능"""
    try:
        result = account_DB.fetch_student_name(payload.univ_id)
        if isinstance(result, Exception) or result is None:
            logger.error(f"Error in find student name operation for univ_id {payload.univ_id}: {str(result)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error in find student name Operation: {str(result)}")
        logger.info(f"Student name found for univ_id {payload.univ_id}: {result}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Find Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.error(f"Unexpected error in find student name operation for univ_id {payload.univ_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error in find student name Operation: {str(e)}")

@router.post("/acc/load_dept")
async def api_acc_load_department():
    """모든 학과를 조회하는 기능"""
    try:
        result = account_DB.fetch_dept_list()
        if isinstance(result, Exception):
            logger.error(f"Error in load dept operation: {str(result)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error in load dept Operation: {str(result)}")
        logger.info("Department list retrieved successfully")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Load Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.error(f"Unexpected error in load dept operation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error in load dept Operation: {str(e)}")

@router.post("/acc/load_prof")
async def api_acc_load_professor_by_subject(payload: LoadProfPayload):
    """특정 교과목이 속한 학과의 교수 리스트를 불러오는 기능"""
    try:
        result = account_DB.fetch_professor_list_by_subject(payload.subj_no)
        if isinstance(result, Exception):
            logger.error(f"Error in load professor operation for subject {payload.subj_no}: {str(result)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error in load professor operation: {str(result)}")
        logger.info(f"Professor list retrieved successfully for subject {payload.subj_no}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Load Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.error(f"Unexpected error in load professor operation for subject {payload.subj_no}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error in load professor operation: {str(e)}")
