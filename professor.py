"""
   CodeCraft PMS Backend Project

   파일명   : professor.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2025/03/17
   업데이트 : 2025/03/17
                                                                              
   설명     : 교수 계정 관련 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from logger import logger
import sys, os, random, string, logging

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import project_DB
import account_DB

router = APIRouter()

class Signin_Payload(BaseModel):
    id: str
    pw: str

class Token_Payload(BaseModel):
    token: str

class Checksession_Payload(BaseModel):
    user_id: str
    token: str

class Profnum_Payload(BaseModel):
    f_no: int


def generate_token():
    """랜덤한 15자리 토큰 생성"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=15))

@router.post("/prof/checksession")
async def api_prof_check_session(payload: Checksession_Payload):
    """세션 유효성 확인"""
    try:
        is_valid = account_DB.validate_professor_token(payload.user_id, payload.token)
        if isinstance(is_valid, Exception):
            logger.error(f"Invalid session for professor {payload.user_id}: {str(is_valid)}", exc_info=True)
            raise HTTPException(status_code=401, detail=f"Invalid session: {str(is_valid)}")
        if is_valid:
            logger.info(f"Session valid for professor {payload.user_id}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Session valid"}
        logger.warning(f"Invalid session token for professor {payload.user_id}")
        raise HTTPException(status_code=401, detail="Invalid session token")
    except Exception as e:
        logger.error(f"Unexpected error validating session for professor {payload.user_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error validating session: {str(e)}")

@router.post("/prof/signin")
async def api_prof_signin_post(payload: Signin_Payload):
    """사용자 로그인"""
    try:
        f_no = account_DB.validate_professor(payload.id, payload.pw)
        if f_no is None:
            logger.warning(f"Invalid login attempt: {payload.id}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if isinstance(f_no, Exception):
            logger.error(f"Internal error during validation: {str(f_no)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal error during validation: {str(f_no)}")
        token = generate_token()
        save_result = account_DB.save_signin_professor_token(payload.id, token)
        if isinstance(save_result, Exception):
            logger.error(f"Error saving session token for professor {payload.id}: {str(save_result)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error saving session token: {str(save_result)}")
        logger.info(f"User {payload.id} signed in successfully")
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Login successful",
            "PAYLOADS": {
                "Token": token,
                "Univ_ID": f_no
            }
        }
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logger.error(f"Unhandled exception during login for user {payload.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unhandled exception during login: {str(e)}")

@router.post("/prof/signout")
async def api_prof_signout_post(payload: Token_Payload):
    """사용자 로그아웃"""
    try:
        result = account_DB.signout_user(payload.token)
        if isinstance(result, Exception):
            logger.error(f"Error during logout: {str(result)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error during logout: {str(result)}")
        if result is True:
            logger.info("Professor logged out successfully")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Logout successful"}
        logger.warning("Logout failed")
        raise HTTPException(status_code=500, detail="Logout failed")
    except Exception as e:
        logger.error(f"Unhandled exception during logout: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unhandled exception during logout: {str(e)}")

@router.post("/prof/check_acc")
async def api_prof_check_account_type(payload: Token_Payload):
    """이 계정이 학생인지 교수인지 확인하는 함수"""
    try:
        result = account_DB.check_user_type(payload.token)
        if isinstance(result, Exception):
            logger.info(f"function api_prof_check_account_type failed: {str(result)}")
            raise HTTPException(status_code=500, detail=f"check_acc failed")
        elif result == 0:
            logger.warning(f"function waring api_prof_check_account_type: Token {payload.token} isn't found in the database.")
            raise HTTPException(status_code=404, detail=f"Token {payload.token} isn't found in the database.")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Check Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.error(f"Error while check account token {payload.token}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error in check token operation: {str(e)}")

@router.post("/prof/load_project")
async def api_prof_load_project_info(payload: Profnum_Payload):
    """교수용 프로젝트 로드 함수"""
    try:
        result = project_DB.fetch_project_info_for_professor(payload.f_no)
        if isinstance(result, Exception):
            logger.info(f"function api_prof_load_project_info failed: {str(result)}")
            raise HTTPException(status_code=500, detail=f"load_project failed")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Check Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.error(f"Error while load project {payload.f_no}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error in load project operation: {str(e)}")