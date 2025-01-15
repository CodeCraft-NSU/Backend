"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : permission.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2025/01/15                                                   
   업데이트 : 2025/01/15                                            
                                                                             
   설명     : 계정의 프로젝트 접근 권한을 조회하는 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys, os, requests

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import permission_DB

router = APIRouter()

class PermissionPayload(BaseModel):
    pid: int
    univ_id: int

class PMListPayload(BaseModel):
    pid: int
    univ_id: int = None


def api_add_leader_permission(pid, univ_id):
    return ""

@router.post("/pm/add_ro")
async def api_add_ro_permission(payload: PermissionPayload):
    return {}

@router.post("/pm/add_ro2")
async def api_add_ro2_permission(payload: PermissionPayload):
    return {}

@router.post("/pm/add_default")
async def api_add_default_permission(payload: PermissionPayload):
    return ""

@router.post("/pm/add_manual")
async def api_add_manual_permission(payload: PMListPayload):
    return ""

@router.post("/pm/edit_manual")
async def api_edit_manual_permission(payload: PMListPayload):
    return ""

@router.post("/pm/load_one")
async def api_load_pm_one(payload: PermissionPayload):
    return ""

@router.post("/pm/load_all")
async def api_load_pm_all(payload: PermissionPayload):
    return ""

@router.post("/pm/check_leader")
async def api_check_leader(payload: PermissionPayload):
    return ""