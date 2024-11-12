"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : project.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/10/16                                                      
   업데이트 : 2024/10/29                                                      
                                                                             
   설명     : 프로젝트의 생성, 수정, 조회를 위한 API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import random # gen_project_uid 함수에서 사용
import sys, os

sys.path.append(os.path.abspath('/data/Database Project')) # Database Project와 연동하기 위해 사용
import project_DB

router = APIRouter()

class project_init(BaseModel): # 프로젝트 생성 클래스
    pname: str # 프로젝트 이름
    pdetails: str # 프로젝트 내용
    psize: int # 프로젝트 개발 인원
    pperiod: str # 프로젝트 개발 기간 241012-241130
    pmm: int # 프로젝트 관리 방법론; project management methodologies

class project_edit(BaseModel): # 프로젝트 수정 클래스
    pid: int # 프로젝트의 고유번호
    pname: str # 프로젝트 이름
    pdetails: str # 프로젝트 내용
    psize: int # 프로젝트 개발 인원
    pperiod: str # 프로젝트 개발 기간; 241012-241130
    pmm: int # 프로젝트 관리 방법론; project management methodologies

class project_load(BaseModel): #프로젝트 로드 클래스
    univ_id: int # 학번으로 자신이 소유한 프로젝트를 불러옴

class project_delete(BaseModel):
    pid = str

class project_loaduser(BaseModel):  # 팀원 조회 클래스
    pid: int  # 프로젝트 고유번호

class project_adduser(BaseModel):  # 팀원 추가 클래스
    pid: int  # 프로젝트 고유번호
    univ_id: int  # 학번
    role: str  # 팀원 역할

class project_deleteuser(BaseModel):  # 팀원 삭제 클래스
    pid: int  # 프로젝트 고유번호
    univ_id: int  # 학번

class project_edituser(BaseModel):  # 팀원 수정 클래스
    id: int  # 수정할 팀원의 ID
    name: str  # 수정할 이름
    email: str  # 수정할 이메일
    univ_id: int  # 학번
    pid: int  # 프로젝트 고유번호
    role: str  # 수정할 역할

class project_checkpm(BaseModel):  # PM 권한 확인 클래스
    pid: int  # 프로젝트 고유번호
    univ_id: int  # 학번

def gen_project_uid(): # 프로젝트 고유 ID 생성 함수
    """
    5자의 수열을 무작위로 만들되, DB와 통신해서 중복되지 않은 수열인지 먼저 체크 후 return함
    """
    tmp_uid = 0

    def check_uid(): # DB와 통신해서 UID의 중복을 확인하는 함수
        session = db_connect()
        # 개쩌는 통신 기능 구현
        if result is False: return False
        else: return True

    while True:
        tmp_uid = random.randint(10000, 99999)
        if check_uid is False: # 이미 있는 UID 값이라면
            continue # 될 때까지 재시도
        else: break

    return tmp_uid # 최종 uid값 return

@router.post("/project/init")
async def api_prj_init_post(payload: project_init):
    """
    DB에 payload로 전달받은 정보를 기입하는 쿼리 실행
    project_DB의 init_project()를 사용함
    """
    PUID = gen_project_uid()
    if project_DB.init_result(payload, PUID) is True:
        return {"RESULT_CODE": 200,
                "RESULT_MSG": "Success",
                "PAYLOADS": {
                                "result": "OK",
                                "PUID": PUID
                            }}
    else:
        return {"RESULT_CODE": 500,
                "RESULT_MSG": "Error",
                "PAYLOADS": {
                                "result": "" # 에러 내용을 DB로부터 파싱해서 기입..
                            }}

@router.post("/project/edit")
async def api_prj_edit_post(payload: project_edit):
    """
    DB에 payload로 전달받은 정보를 수정하는 쿼리 실행
    project_DB의 edit_project 사용
    """
    if project_DB.edit_project(payload):
        return {"RESULT_CODE": 200,
                "RESULT_MSG": "Success",
                "PAYLOADS": {}}
    else:
        return {"RESULT_CODE": 500,
                "RESULT_MSG": "Internal Server Error",
                "PAYLOADS": {}}

@router.post("/project/load")
async def api_prj_load_post(payload: project_load):
    """
    DB에서 데이터를 가져오는 쿼리 실행
    project_info = fetch_project_info(payload.univ_id) 학번을 기준으로 프로젝트 정보 조회
    """
    project_info = project_DB.fetch_project_info(payload.univ_id)
    if project_info is False:
        return {
            "RESULT_CODE": 500,
            "RESULT_MSG": "Internal Server Error",
            "PAYLOADS": {}
        }

    payloads = []
    for project in project_info:
        pperiod = project["p_start"] + "-" + project["p_end"]
        payloads.append({
            "pid": project["p_no"],  # p.p_no
            "pname": project["p_name"],  # p.p_name
            "pdetails": project["p_content"],  # p.p_content
            "psize": project["p_memcount"],  # p.p_memcount
            "pperiod": pperiod,  # p.p_start, p.p_end
            "pmm": project["p_method"]  # p.p_method
        })

    return {
        "RESULT_CODE": 200,
        "RESULT_MSG": "Success",
        "PAYLOADS": payloads
    }

@router.post("/prj/loaduser")
async def api_prj_loaduser_post(payload: project_loaduser):
    """
    프로젝트에 참여 중인 모든 팀원 조회
    """
    users = project_DB.fetch_project_user(payload.pid)
    if users is False:
        return {
            "RESULT_CODE": 500,
            "RESULT_MSG": "Internal Server Error",
            "PAYLOADS": {}
        }
    
    payloads = [
        {
            "univ_id": user["s_no"],
            "role": user["role"],
            "permission": user["permission"]
        } for user in users
    ]
    return {
        "RESULT_CODE": 200,
        "RESULT_MSG": "Success",
        "PAYLOADS": payloads
    }

@router.post("/prj/delete")
async def api_prj_delete_post(payload: project_delete):
    if project_DB.delete_project(payload.pid):
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Success",
            "PAYLOADS": {}}
    else:
        return {
            "RESULT_CODE": 500,
            "RESULT_MSG": "Internal Server Error",
            "PAYLOADS": {}}

@router.post("/prj/adduser")
async def api_prj_adduser_post(payload: project_adduser):
    """
    프로젝트에 팀원 추가
    """
    if project_DB.add_project_user(payload.pid, payload.univ_id, payload.role):
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Success",
            "PAYLOADS": {}
        }
    else:
        return {
            "RESULT_CODE": 500,
            "RESULT_MSG": "Internal Server Error",
            "PAYLOADS": {}
        }

@router.post("/prj/deleteuser")
async def api_prj_deleteuser_post(payload: project_deleteuser):
    """
    프로젝트에서 팀원 삭제
    """
    if project_DB.delete_project_user(payload.pid, payload.univ_id):
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Success",
            "PAYLOADS": {}
        }
    else:
        return {
            "RESULT_CODE": 500,
            "RESULT_MSG": "Internal Server Error",
            "PAYLOADS": {}
        }

@router.post("/prj/edituser")
async def api_prj_edituser_post(payload: project_edituser):
    """
    팀원 정보 수정
    """
    if project_DB.edit_project_user(payload.id, payload.name, payload.email, payload.univ_id, payload.pid, payload.role):
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Success",
            "PAYLOADS": {}
        }
    else:
        return {
            "RESULT_CODE": 500,
            "RESULT_MSG": "Internal Server Error",
            "PAYLOADS": {}
        }

@router.post("/prj/checkpm")
async def api_rpj_checkpm_post(payload: project_checkpm):
    """
    PM 권한 확인
    """
    has_permission = project_DB.validate_pm_permission(payload.pid, payload.univ_id)
    if has_permission:
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Success",
            "PAYLOADS": {
                "permission": "granted"
            }
        }
    else:
        return {
            "RESULT_CODE": 403,
            "RESULT_MSG": "Forbidden",
            "PAYLOADS": {
                "permission": "denied"
            }
        }