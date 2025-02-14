"""
   CodeCraft PMS Backend Project

   파일명   : subject.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2025/02/14                                             
   업데이트 : 2025/02/14                                      
                                                                              
   설명     : 교과목 관련 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys, os

sys.path.append(os.path.abspath('/data/Database Project'))
import subject_DB

router = APIRouter()

class SubjectPayload(BaseModel):
    dno: int = None
    univ_id: int = None

@router.post("/subject/load_all")
async def api_subject_load_all():
    """등록된 모든 과목을 조회"""
    try:
        result = fetch_subject_list()
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error in Load all Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Load Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in Load all Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in Load all Operation: {str(e)}")

@router.post("/subject/load_dept")
async def api_subject_load_by_dept(payload: SubjectPayload):
    """특정 학과의 모든 과목을 조회"""
    try:
        result = fetch_subject_list_of_dept(payload.dno)
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error in Load dept Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Load Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in Load all Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in Load dept Operation: {str(e)}")

@router.post("/subject/load_student")
async def api_subject_load_by_student(payload: SubjectPayload):
    """특정 학생이 속한 학과의 모든 과목을 조회"""
    try:
        result = fetch_subject_list_of_student(payload.univ_id)
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error in Load student Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Load Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in Load all Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in Load student Operation: {str(e)}")