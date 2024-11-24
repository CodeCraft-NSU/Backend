"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : project.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/10/16                                                      
   업데이트 : 2024/11/19                                                      
                                                                             
   설명     : 프로젝트의 생성, 수정, 조회를 위한 API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import random  # gen_project_uid 함수에서 사용
import sys, os, requests

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import project_DB

router = APIRouter()

# 데이터 모델 정의
class ProjectInit(BaseModel):  
    """프로젝트 생성 클래스"""
    pname: str  # 프로젝트 이름
    pdetails: str  # 프로젝트 내용
    psize: int  # 프로젝트 개발 인원
    pperiod: str  # 프로젝트 개발 기간 (예: "241012-241130")
    pmm: int  # 프로젝트 관리 방법론 (프로젝트 관리 방식)


class ProjectEdit(BaseModel):  
    """프로젝트 수정 클래스"""
    pid: int  # 프로젝트의 고유번호
    pname: str  # 프로젝트 이름
    pdetails: str  # 프로젝트 내용
    psize: int  # 프로젝트 개발 인원
    pperiod: str  # 프로젝트 개발 기간 (예: "241012-241130")
    pmm: int  # 프로젝트 관리 방법론 (프로젝트 관리 방식)


class ProjectLoad(BaseModel):  
    """프로젝트 로드 클래스 (프로젝트 조회 요청)"""
    univ_id: int  # 학번 (조회 대상 학생의 학번)


class ProjectDelete(BaseModel):  
    """프로젝트 삭제 클래스"""
    pid: int  # 삭제하려는 프로젝트의 고유번호


class ProjectLoadUser(BaseModel):  
    """프로젝트 팀원 조회 클래스"""
    pid: int  # 프로젝트 고유번호 (팀원을 조회하려는 프로젝트의 번호)


class ProjectAddUser(BaseModel):  
    """프로젝트 팀원 추가 클래스"""
    pid: int  # 프로젝트 고유번호
    univ_id: int  # 추가하려는 팀원의 학번
    role: str  # 팀원의 역할 (예: "developer", "designer", "PM")


class ProjectDeleteUser(BaseModel):  
    """프로젝트 팀원 삭제 클래스"""
    pid: int  # 프로젝트 고유번호
    univ_id: int  # 삭제하려는 팀원의 학번


class ProjectEditUser(BaseModel):  
    """프로젝트 팀원 수정 클래스"""
    univ_id: int  # 팀원의 학번
    pid: int  # 팀원이 소속된 프로젝트의 고유번호
    role: str  # 팀원의 역할 (수정된 역할)

class ProjectCheckPM(BaseModel):  
    """PM 권한 확인 클래스"""
    pid: int  # 프로젝트 고유번호
    univ_id: int  # 확인하려는 사용자의 학번

# 유틸리티 함수
def gen_project_uid():
    """프로젝트 고유 ID 생성"""
    while True:
        tmp_uid = random.randint(10000, 99999)
        if not project_DB.is_uid_exists(tmp_uid): return tmp_uid

def init_file_system(PUID):
    load_dotenv()
    headers = {"Authorization": os.getenv('ST_KEY')}
    data = {"PUID": PUID}
    try:
        response = requests.post("http://192.168.50.84:10080/api/project/init", json=data, headers=headers)
        if response.status_code == 200: return True
        else: print(f"Error: {response.status_code} - {response.text}"); return False
    except requests.exceptions.RequestException as e: 
        print(f"Request failed: {e}"); return False

# API 엔드포인트
@router.post("/project/init")
async def api_project_init(payload: ProjectInit):
    """프로젝트 생성 및 초기화"""
    try:
        # 1. 프로젝트 고유 ID 생성
        PUID = gen_project_uid()
        # 2. 프로젝트 데이터베이스 초기화
        db_result = project_DB.init_project(payload, PUID)
        if not db_result:
            raise HTTPException(
                status_code=500,
                detail=f"Database initialization failed for PUID: {PUID}",
            )
        # 3. 파일 시스템 초기화
        file_result = init_file_system(PUID)
        if not file_result:
            # 파일 시스템 초기화 실패 시 방금 생성된 프로젝트 삭제
            delete_result = project_DB.delete_project(PUID)
            if not delete_result:
                raise HTTPException(
                    status_code=500,
                    detail=f"File system initialization failed for PUID: {PUID}, and cleanup also failed.",
                )
            raise HTTPException(
                status_code=500,
                detail=f"File system initialization failed for PUID: {PUID}. Project deleted successfully.",
            )
        # 4. 성공 응답 반환
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Project created successfully",
            "PAYLOADS": {"PUID": PUID},
        }
    except HTTPException as http_exc:
        # HTTPException은 그대로 전달
        raise http_exc
    except Exception as e:
        # 알 수 없는 예외 처리
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during project creation: {str(e)}",
        )

@router.post("/project/edit")
async def api_project_edit(payload: ProjectEdit):
    """프로젝트 수정"""
    try:
        result = project_DB.edit_project(payload)
        if result is True:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Project updated successfully"}
        raise HTTPException(status_code=500, detail="Project update failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during project update: {str(e)}")


@router.post("/project/load")
async def api_project_load(payload: ProjectLoad):
    """프로젝트 조회"""
    try:
        project_info = project_DB.fetch_project_info(payload.univ_id)
        if not project_info:
            raise HTTPException(status_code=404, detail="No projects found")

        payloads = [
            {
                "pid": project["p_no"],
                "pname": project["p_name"],
                "pdetails": project["p_content"],
                "psize": project["p_memcount"],
                "pperiod": f"{project['p_start']}-{project['p_end']}",
                "pmm": project["p_method"],
            }
            for project in project_info
        ]

        return {"RESULT_CODE": 200, "RESULT_MSG": "Projects loaded successfully", "PAYLOADS": payloads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during project load: {str(e)}")


@router.post("/project/delete")
async def api_project_delete(payload: ProjectDelete):
    """프로젝트 삭제"""
    try:
        result = project_DB.delete_project(payload.pid)
        if result is True:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Project deleted successfully"}
        raise HTTPException(status_code=500, detail="Project deletion failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during project deletion: {str(e)}")


@router.post("/project/adduser")
async def api_project_add_user(payload: ProjectAddUser):
    """팀원 추가"""
    try:
        result = project_DB.add_project_user(payload.pid, payload.univ_id, 0, payload.role)
        if result is True:
            return {"RESULT_CODE": 200, "RESULT_MSG": "User added to project successfully"}
        raise HTTPException(status_code=500, detail="Failed to add user to project")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during user addition: {str(e)}")


@router.post("/project/deleteuser")
async def api_project_delete_user(payload: ProjectDeleteUser):
    """팀원 삭제"""
    try:
        result = project_DB.delete_project_user(payload.pid, payload.univ_id)
        if result is True:
            return {"RESULT_CODE": 200, "RESULT_MSG": "User removed from project successfully"}
        raise HTTPException(status_code=500, detail="Failed to remove user from project")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during user removal: {str(e)}")


@router.post("/project/edituser")
async def api_project_edit_user(payload: ProjectEditUser):
    """팀원 정보 수정"""
    try:
        result = project_DB.edit_project_user(payload.id, payload.name, payload.email, payload.univ_id, payload.pid, payload.role)
        if result is True:
            return {"RESULT_CODE": 200, "RESULT_MSG": "User updated successfully"}
        raise HTTPException(status_code=500, detail="Failed to update user")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during user update: {str(e)}")


@router.post("/project/checkpm")
async def api_project_check_pm(payload: ProjectCheckPM):
    """PM 권한 확인"""
    try:
        has_permission = project_DB.validate_pm_permission(payload.pid, payload.univ_id)
        if has_permission:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Permission granted"}
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during permission check: {str(e)}")

@router.post("/project/checkuser")
async def api_project_check_user(pid: str):
    """
    프로젝트 참여자 확인
    """
    try:
        # 프로젝트 참여자 목록 가져오기
        users = project_DB.fetch_project_user(pid)
        # 데이터베이스 호출 실패 처리
        if isinstance(users, Exception):
            raise HTTPException(status_code=500, detail=f"Error fetching project users: {str(users)}")
        # 프로젝트에 참여자가 없는 경우 처리
        if not users:
            raise HTTPException(status_code=404, detail="Project not found or has no users")
        # 참여자 목록 반환
        payloads = [
            {
                "univ_id": user["s_no"],
                "role": user["role"],
                "permission": user["permission"]
            }
            for user in users
        ]
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Project users retrieved successfully",
            "PAYLOADS": payloads
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking project users: {str(e)}")