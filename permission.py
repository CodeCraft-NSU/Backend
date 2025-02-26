"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : permission.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2025/01/15                                                   
   업데이트 : 2025/01/16                                         
                                                                             
   설명     : 계정의 프로젝트 접근 권한을 조회하는 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from logger import logger
import sys, os, requests, traceback

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import permission_DB

router = APIRouter()

class PermissionPayload(BaseModel):
    pid: int
    univ_id: int = None

class PMListPayload(BaseModel):
    pid: int
    univ_id: int
    user: int
    wbs: int
    od: int
    mm: int
    ut: int
    rs: int
    rp: int
    om: int
    task: int
    llm: int

def add_leader_permission(pid, univ_id):
    result = permission_DB.add_leader_permission(pid, univ_id)
    if isinstance(result, Exception):
        print(f"Error occurred: {result}")
        return False
    if result: return True
    else: return False

def handle_db_result(result):
    if isinstance(result, Exception):
        print(f"Database error: {result}")
        return False
    return result

@router.post("/pm/add_leader")
async def api_add_leader_permission(payload: PermissionPayload):
    try:
        result = permission_DB.add_leader_permission(payload.pid, payload.univ_id)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error adding leader permission: {e}")
    
    if not handle_db_result(result):
        return {"RESULT_CODE": 500, "RESULT_MSG": "Failed to add leader permission"}
    return {"RESULT_CODE": 200, "RESULT_MSG": "Leader permission added successfully"}

@router.post("/pm/add_ro")
async def api_add_ro_permission(payload: PermissionPayload):
    try:
        result = permission_DB.add_ro_permission(payload.pid, payload.univ_id)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error adding RO permission: {e}")

    if not handle_db_result(result):
        return {"RESULT_CODE": 500, "RESULT_MSG": "Failed to add RO permission"}
    return {"RESULT_CODE": 200, "RESULT_MSG": "RO permission added successfully"}

@router.post("/pm/add_ro2")
async def api_add_ro2_permission(payload: PermissionPayload):
    try:
        result = permission_DB.add_ro_permission2(payload.pid, payload.univ_id)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error adding RO2 permission: {e}")

    if not handle_db_result(result):
        return {"RESULT_CODE": 500, "RESULT_MSG": "Failed to add RO2 permission"}
    return {"RESULT_CODE": 200, "RESULT_MSG": "RO2 permission added successfully"}

@router.post("/pm/add_default")
async def api_add_default_permission(payload: PermissionPayload):
    try:
        result = permission_DB.add_default_user_permission(payload.pid, payload.univ_id)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error adding default permission: {e}")

    if not handle_db_result(result):
        return {"RESULT_CODE": 500, "RESULT_MSG": "Failed to add default permission"}
    return {"RESULT_CODE": 200, "RESULT_MSG": "Default permission added successfully"}

@router.post("/pm/add_manual")
async def api_add_manual_permission(payload: PMListPayload):
    try:
        result = permission_DB.add_manual_permission(
            pid=payload.pid,
            univ_id=payload.univ_id,
            leader=0,
            ro=0,
            user=payload.user,
            wbs=payload.wbs,
            od=payload.od,
            mm=payload.mm,
            ut=payload.ut,
            rs=payload.rs,
            rp=payload.rp,
            om=payload.om,
            task=payload.task,
            llm=payload.llm
        )
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error adding manual permission: {e}")

    if not handle_db_result(result):
        return {"RESULT_CODE": 500, "RESULT_MSG": "Failed to add manual permission"}
    return {"RESULT_CODE": 200, "RESULT_MSG": "Manual permission added successfully"}

@router.post("/pm/edit_manual")
async def api_edit_manual_permission(payload: PMListPayload):
    try:
        result = permission_DB.edit_permission(
            pid=payload.pid,
            univ_id=payload.univ_id,
            leader=0,
            ro=0,
            user=payload.user,
            wbs=payload.wbs,
            od=payload.od,
            mm=payload.mm,
            ut=payload.ut,
            rs=payload.rs,
            rp=payload.rp,
            om=payload.om,
            task=payload.task,
            llm=payload.llm
        )
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error editing manual permission: {e}")

    if not handle_db_result(result):
        return {"RESULT_CODE": 500, "RESULT_MSG": "Failed to edit manual permission"}
    return {"RESULT_CODE": 200, "RESULT_MSG": "Manual permission edited successfully"}

@router.post("/pm/load_one")
async def api_load_pm_one(payload: PermissionPayload):
    try:
        result = permission_DB.fetch_all_permissions_of_user(payload.pid, payload.univ_id)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error loading user permissions: {e}")

    if not handle_db_result(result):
        return {"RESULT_CODE": 500, "RESULT_MSG": "Failed to load user permissions"}
    return {"RESULT_CODE": 200, "RESULT_MSG": result}

@router.post("/pm/load_all")
async def api_load_pm_all(payload: PermissionPayload):
    try:
        result = permission_DB.fetch_all_permissions_of_all_users(payload.pid)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error loading all user permissions: {e}")

    if not handle_db_result(result):
        return {"RESULT_CODE": 500, "RESULT_MSG": "Failed to load all user permissions"}
    return {"RESULT_CODE": 200, "RESULT_MSG": result}


@router.post("/pm/check_leader")
async def api_check_leader(payload: PermissionPayload):
    result = permission_DB.validate_leader_permission(payload.pid, payload.univ_id)
    if isinstance(result, Exception):
        print(f"Error occurred: {result}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "False"}
    if result: 
        return {"RESULT_CODE": 200, "RESULT_MSG": "True"}
    else:
        return {"RESULT_CODE": 200, "RESULT_MSG": "False"}