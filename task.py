"""                                                          
   CodeCraft PMS Backend Project          

   파일명   : task.py                                                          
   생성자   : 김창환     
                                                  
   생성일   : 2024/10/20                                                      
   업데이트 : 2025/03/08

   설명     : 작업의 생성, 수정, 조회, 삭제를 위한 API 엔드포인트 정의 및 확장
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from logger import logger
import sys, os

sys.path.append(os.path.abspath('/data/Database Project')) # Database Project와 연동하기 위해 사용
import task_DB

router = APIRouter()

class TaskLoadPayload(BaseModel):
    pid: int
    univ_id: int = None

class TaskAddPayload(BaseModel):
    tname: str
    tperson: str
    tstart: str
    tend: str
    pid: int
    univ_id: int

class TaskEditPayload(BaseModel):
    tname: str
    tperson: str
    tstart: str
    tend: str
    tfinish: bool
    univ_id: int
    tid: int

class TaskDeletePayload(BaseModel):
    tid: int

@router.post("/task/load")
async def load_tasks(payload: TaskLoadPayload):
    """특정 프로젝트 및 사용자의 업무 조회"""
    try:
        task_info_list = task_DB.fetch_task_info(payload.pid, payload.univ_id)
        if not task_info_list:
            logger.info(f"No tasks found for project {payload.pid}, user {payload.univ_id}")
            return {"RESULT_CODE": 404, "RESULT_MSG": "No tasks found for the given project and user."}
        tasks = [
            {
                "tid": task["w_no"],
                "tname": task["w_name"],
                "tperson": task["w_person"],
                "tstart": task["w_start"],
                "tend": task["w_end"],
                "tfinish": task["w_checked"],
                "univ_id": task["s_no"]
            }
            for task in task_info_list
        ]
        logger.info(f"Successfully loaded {len(tasks)} tasks for project {payload.pid}, user {payload.univ_id}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Success", "PAYLOADS": tasks}
    except Exception as e:
        logger.error(f"Error while loading tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error while loading tasks: {str(e)}")

@router.post("/task/load_all")
async def load_tasks_all(payload: TaskLoadPayload):
    """프로젝트 내 모든 업무 조회"""
    try:
        tasks = task_DB.fetch_all_task_info(payload.pid)
        logger.info(f"Successfully loaded {len(tasks)} tasks for project {payload.pid}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Tasks fetched successfully", "PAYLOADS": tasks}
    except Exception as e:
        logger.error(f"Error while fetching all tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching all tasks: {str(e)}")

@router.post("/task/add")
async def add_task(payload: TaskAddPayload):
    """업무 추가"""
    try:
        task_id = task_DB.add_task_info(
            tname=payload.tname,
            tperson=payload.tperson,
            tstart=payload.tstart,
            tend=payload.tend,
            pid=payload.pid,
            univ_id=payload.univ_id,
        )
        if isinstance(task_id, Exception):
            raise task_id
        logger.info(f"Task '{payload.tname}' added successfully with ID {task_id}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Task added successfully.", "PAYLOADS": {"task_id": task_id}}
    except Exception as e:
        logger.error(f"Error while adding task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error while adding task: {str(e)}")

@router.post("/task/edit")
async def edit_task(payload: TaskEditPayload):
    """업무 수정"""
    try:
        success = task_DB.update_task_info(
            tname=payload.tname,
            tperson=payload.tperson,
            tstart=payload.tstart,
            tend=payload.tend,
            tfinish=payload.tfinish,
            univ_id=payload.univ_id,
            w_no=payload.tid,
        )
        if not success:
            raise Exception("Task update failed.")
        logger.info(f"Task {payload.tid} updated successfully for project {payload.pid}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Task updated successfully."}
    except Exception as e:
        logger.error(f"Error while editing task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error while editing task: {str(e)}")

@router.post("/task/delete")
async def delete_task(payload: TaskDeletePayload):
    """업무 삭제"""
    try:
        success = task_DB.delete_task_info(payload.tid)
        if not success:
            raise Exception("Task deletion failed.")
        logger.info(f"Task {payload.tid} deleted successfully")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Task deleted successfully."}
    except Exception as e:
        logger.error(f"Error while deleting task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error while deleting task: {str(e)}")
