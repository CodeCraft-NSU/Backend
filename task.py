# 일정 관련 기능
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import mysql_connection # MySQL 연결 기능 수행

router = APIRouter()

class task_load(BaseModel): #업무관리 로드 클래스
    univ_id: int # 학번으로 자신이 소유한 업무를 불러옴

@router.get("/task/load")
async def api_tsk_load_get(payload: task_load):
    db_connect()  # DB에 접속
    """
    DB에서 데이터를 가져오는 쿼리 실행
    예시로, 가상의 함수 fetch_task_info()를 사용한다고 가정
    task_info = fetch_task_info(payload.univ_id) 학번을 기준으로 프로젝트 정보 조회
    """
    task_info_list = fetch_task_info(payload.univ_id)  # 여러 task 정보를 리스트로 가져온다고 가정

    if not task_info_list:
        raise HTTPException(status_code=404, detail="Task not found")  # 프로젝트가 없는 경우 예외 처리
    
    # 여러 개의 task_info를 처리
    tasks = []
    for task_info in task_info_list:
        tid = task_info['tid']
        tname = task_info['tname']
        tperson = task_info['tperson']
        tstart = task_info['tstart']
        tend = task_info['tend']
        tfinish = task_info['tfinish']
        
        tasks.append({
            "tid": tid,
            "tname": tname,
            "tperson": tperson,
            "tstart": tstart,
            "tend": tend,
            "tfinish": tfinish
        })
    
    return tasks  # 리스트로 반환
