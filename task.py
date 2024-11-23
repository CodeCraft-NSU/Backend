"""                                                          
   CodeCraft PMS Backend Project          

   파일명   : task.py                                                          
   생성자   : 김창환     
                                                  
   생성일   : 2024/10/20                                                      
   업데이트 : 2024/11/23       

   설명     : 작업의 생성, 수정, 조회, 삭제를 위한 API 엔드포인트 정의 및 확장
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys, os

sys.path.append(os.path.abspath('/data/Database Project')) # Database Project와 연동하기 위해 사용
import task_DB

router = APIRouter()

class TaskLoadPayload(BaseModel):
    pid: int
    univ_id: int

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
    tid: int

class TaskDeletePayload(BaseModel):
    tid: int

# 업무 조회
@router.post("/task/load")
async def load_tasks(payload: TaskLoadPayload):
    try:
        task_info_list = task_DB.fetch_task_info(payload.pid, payload.univ_id)
        if not task_info_list:
            return {"RESULT_CODE": 404, "RESULT_MSG": "No tasks found for the given project and user."}
        
        tasks = [
            {
                "tid": task["w_no"],
                "tname": task["w_name"],
                "tperson": task["w_person"],
                "tstart": task["w_start"],
                "tend": task["w_end"],
                "tfinish": task["w_checked"],
            }
            for task in task_info_list
        ]

        return {"RESULT_CODE": 200, "RESULT_MSG": "Success", "PAYLOADS": tasks}

    except Exception as e:
        return {"RESULT_CODE": 500, "RESULT_MSG": str(e)}

# 업무 추가
@router.post("/task/add")
async def add_task(payload: TaskAddPayload):
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

        return {"RESULT_CODE": 200, "RESULT_MSG": "Task added successfully.", "PAYLOADS": {"task_id": task_id}}

    except Exception as e:
        return {"RESULT_CODE": 500, "RESULT_MSG": str(e)}

# 업무 수정
@router.post("/task/edit")
async def edit_task(payload: TaskEditPayload):
    try:
        success = task_DB.update_task_info(
            tname=payload.tname,
            tperson=payload.tperson,
            tstart=payload.tstart,
            tend=payload.tend,
            tfinish=payload.tfinish,
            w_no=payload.tid,
        )
        if not success:
            raise HTTPException(status_code=500, detail="Task update failed.")

        return {"RESULT_CODE": 200, "RESULT_MSG": "Task updated successfully."}

    except Exception as e:
        return {"RESULT_CODE": 500, "RESULT_MSG": str(e)}

# 업무 삭제
@router.post("/task/delete")
async def delete_task(payload: TaskDeletePayload):
    try:
        success = task_DB.delete_task_info(payload.tid)
        if not success:
            raise HTTPException(status_code=500, detail="Task deletion failed.")

        return {"RESULT_CODE": 200, "RESULT_MSG": "Task deleted successfully."}

    except Exception as e:
        return {"RESULT_CODE": 500, "RESULT_MSG": str(e)}