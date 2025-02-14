"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : grade.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/11/24                                                      
   업데이트 : 2025/02/14                                 
                                                                             
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
    univ_id: int = None
    pid: int = None
    comment: str = None

class AssignPayload(BaseModel):
    pid: int
    plan: int
    require: int
    design: int
    progress: int
    scm: int
    cooperation: int
    quality: int
    tech: int
    presentation: int
    completion: int


@router.post("/grade/comment_add")
async def api_grade_add_comment(payload: GradePayload):
    """특정 학생에게 코멘트를 추가 및 수정"""
    try:
        result = grade_DB.add_comment(payload.pid, payload.univ_id, payload.comment)
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error in add comment Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Add Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in add comment Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in add comment Operation: {str(e)}")

@router.post("/grade/comment_del")
async def api_grade_del_comment(payload: GradePayload):
    """특정 학생의 코멘트를 삭제"""
    try:
        result = grade_DB.delete_comment(payload.pid, payload.univ_id)
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error in delete comment Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Delete Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in delete comment Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in delete comment Operation: {str(e)}")

@router.post("/grade/comment_load_student")
async def api_grade_load_comment_one(payload: GradePayload):
    """특정 학생의 모든 코멘트를 조회"""
    try:
        result = grade_DB.fetch_comment_by_student(payload.univ_id)
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error in load one comment Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Load one Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in load one comment Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in load one comment Operation: {str(e)}")

@router.post("/grade/comment_load_project_student")
async def api_grade_load_comment_one_project(payload: GradePayload):
    """특정 프로젝트에 속한 학생의 코멘트를 조회"""
    try:
        result = grade_DB.fetch_one_comment(payload.pid, payload.univ_id)
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error in load one comment project Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Load one Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in load one comment Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in load one comment Operation: {str(e)}")

@router.post("/grade/comment_load_project")
async def api_grade_load_comment_project(payload: GradePayload):
    """특정 프로젝트의 모든 코멘트를 조회"""
    try:
        result = grade_DB.fetch_comment_by_project(payload.pid)
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error in load comment Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Load Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in load comment Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in load comment Operation: {str(e)}")

@router.post("/grade/assign")
async def api_grade_assign(payload: AssignPayload):
    """교수가 프로젝트의 평가를 등록"""
    try:
        result = grade_DB.assign_grade(
            payload.pid, payload.plan, payload.require, payload.design,
            payload.progress, payload.scm, payload.cooperation, payload.quality,
            payload.tech, payload.presentation, payload.completion
        )
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error in assign grade Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Assign Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in assign grade Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in assign grade Operation: {str(e)}")

@router.post("/grade/edit")
async def api_grade_edit(payload: AssignPayload):
    """교수가 프로젝트의 평가를 수정"""
    try:
        result = grade_DB.edit_grade(
            payload.pid, payload.plan, payload.require, payload.design,
            payload.progress, payload.scm, payload.cooperation, payload.quality,
            payload.tech, payload.presentation, payload.completion
        )
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error in edit grade Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Edit Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in edit grade Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in edit grade Operation: {str(e)}")

@router.post("/grade/delete")
async def api_grade_delete(payload: GradePayload):
    """교수가 프로젝트의 평가를 삭제"""
    try:
        result = grade_DB.delete_grade(payload.pid)
        # DB 함수에서 False를 반환할 경우, 해당 프로젝트의 평가가 존재하지 않음을 의미
        if isinstance(result, Exception) or result is False:
            raise HTTPException(status_code=500, detail=f"Error in delete grade Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Delete Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in delete grade Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in delete grade Operation: {str(e)}")

@router.post("/grade/load")
async def api_grade_load(payload: GradePayload):
    """특정 프로젝트의 평가를 조회"""
    try:
        result = grade_DB.fetch_grade(payload.pid)
        if isinstance(result, Exception):
            raise HTTPException(status_code=500, detail=f"Error in load grade Operation: {str(result)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Load Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.debug(f"Error in load grade Operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error in load grade Operation: {str(e)}")