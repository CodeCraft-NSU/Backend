"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : task.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/10/20                                                      
   업데이트 : 2024/10/20                                                      
                                                                             
   설명     : 작업의 생성, 수정, 조회를 위한 API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys, os

sys.path.append(os.path.abspath('/data/Database Project')) # Database Project와 연동하기 위해 사용
import task_DB

router = APIRouter()

class task_load(BaseModel): #업무 로드 클래스
    pid: int
    univ_id: int # 학번으로 자신이 소유한 업무를 불러옴

class task_add(BaseModel): #업무 추가 클래스
    tname: str
    tperson: str
    tstart: str
    tend: str
    pid: int
    univ_id: int

class task_edit(BaseModel): #업무 수정 클래스
    tname: str
    tperson: str
    tstart: str
    tend: str
    tfinish: bool
    tid: int

class task_delete(BaseModel):
    tid: int

# fetch_task_info(pid, univ_id)
@router.get("/task/load")
async def api_tsk_load_get(payload: task_load):
    """
    DB에서 데이터를 가져오는 쿼리 실행
    """
    task_info_list = task_DB.fetch_task_info(payload.pid, payload.univ_id)  # 여러 task 정보를 리스트로 가져온다고 가정

    if not task_info_list:
        return {"RESULT_CODE": 404,
                "RESULT_MSG": "Project Not Found",
                "PAYLOADS": {}}
    
    # 여러 개의 task_info를 처리
    tasks = []
    for task_info in task_info_list:
        tid = task_info['w_no']
        tname = task_info['w_name']
        tperson = task_info['w_person']
        tstart = task_info['w_start']
        tend = task_info['w_end']
        tfinish = task_info['w_checked']
        
        tasks.append({
            "tid": tid,
            "tname": tname,
            "tperson": tperson,
            "tstart": tstart,
            "tend": tend,
            "tfinish": tfinish
        })

    return {"RESULT_CODE": 200,
            "RESULT_MSG": "Success",
            "PAYLOADS": tasks}

@router.post("/task/add")
async def api_tsk_add_post(payload: task_add):
    task_id = add_task_info(
        tname=payload.tname,
        tperson=payload.tperson,
        tstart=payload.tstart,
        tend=payload.tend,
        pid=payload.pid,
        univ_id=payload.univ_id
    )
    
    if task_id is None:
        return {
            "RESULT_CODE": 500,
            "RESULT_MSG": "Internal Server Error",
            "PAYLOADS": {}}
    
    return {
        "RESULT_CODE": 200,
        "RESULT_MSG": "Success",
        "PAYLOADS": {
            "task_id": task_id
        }}


@router.post("/task/edit")
async def api_tsk_edit_post(payload: task_edit):
    updated = update_task_info(
        tname=payload.tname,
        tperson=payload.tperson,
        tstart=payload.tstart,
        tend=payload.tend,
        tfinish=payload.tfinish,
        tid=payload.tid
    )
    
    if not updated:
        return {
            "RESULT_CODE": 500,
            "RESULT_MSG": "Internal Server Error",
            "PAYLOADS": {}}
    
    return {
        "RESULT_CODE": 200,
        "RESULT_MSG": "Success",
        "PAYLOADS": {}}

@router.post("/task/delete")
async def api_tsk_delete_post(payload: task_delete):
    if task_DB.delete_task_info(task_delete.tid):
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Success",
            "PAYLOADS": {}}
    else:
        return {
            "RESULT_CODE": 500,
            "RESULT_MSG": "Internal Server Error",
            "PAYLOADS": {}}