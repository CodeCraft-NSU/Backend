"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : grade.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/11/24                                                      
   업데이트 : 2024/11/24                                              
                                                                             
   설명     : 프로젝트를 평가와 관련 된 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys, os

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import grade_DB

router = APIRouter()

class GradePayload(BaseModel):
    pid: str = None
    univ_id: int = None
    grade: str = None

@router.post("/grade/assign")
async def grade_assign(payload: GradePayload):
    try:
        result = grade_DB.assign_grade(
            pid=payload.pid,
            univ_id=payload.univ_id,
            grade=payload.grade
        )
        if result: return {"RESULT_CODE": 200, "RESULT_MSG": "Assign Successful."}
        else: raise HTTPException(status_code=500, detail="Assign Failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/grade/delete")
async def grade_delete(payload: GradePayload):
    try:
        result = grade_DB.delete_grade(
            pid=payload.pid,
            univ_id=payload.univ_id
        )
        if result: return {"RESULT_CODE": 200, "RESULT_MSG": "Delete Successful."}
        else: raise HTTPException(status_code=500, detail="Delete Failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/grade/fetch_one")
async def fetch_one_grade(payload: GradePayload):
    try:
        result = grade_DB.fetch_one_grade(
            pid=payload.pid,
            univ_id=payload.univ_id
        )
        if result: return {"RESULT_CODE": 200, "RESULT_MSG": "Fetch Successful.", "PAYLOAD": {"Grade": result}}
        else: raise HTTPException(status_code=500, detail=f"Error in Database Operation: {str(result)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/grade/fetch_student")
async def fetch_one_student(payload: GradePayload):
    try:
        result = grade_DB.fetch_grade_by_student(
            univ_id=payload.univ_id
        )
        if result: return {"RESULT_CODE": 200, "RESULT_MSG": "Fetch Successful.", "PAYLOAD": {"Grade": result}}
        else: raise HTTPException(status_code=500, detail=f"Error in Database Operation: {str(result)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/grade/fetch_project")
async def fetch_one_student(payload: GradePayload):
    try:
        result = grade_DB.fetch_grade_by_project(
            pid=payload.pid
        )
        if result: return {"RESULT_CODE": 200, "RESULT_MSG": "Fetch Successful.", "PAYLOAD": {"Grade": result}}
        else: raise HTTPException(status_code=500, detail=f"Error in Database Operation: {str(result)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
