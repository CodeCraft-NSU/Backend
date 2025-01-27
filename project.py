"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : project.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/10/16                                                      
   업데이트 : 2025/01/25                                                  
                                                                             
   설명     : 프로젝트의 생성, 수정, 조회를 위한 API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import random  # gen_project_uid 함수에서 사용
import sys, os, requests
import logging

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import project_DB
import permission
import wbs

router = APIRouter()

# 데이터 모델 정의
class ProjectInit(BaseModel):  
    """프로젝트 생성 클래스"""
    pname: str  # 프로젝트 이름
    pdetails: str  # 프로젝트 내용
    psize: int  # 프로젝트 개발 인원
    pperiod: str  # 프로젝트 개발 기간 (예: "241012-241130")
    pmm: int  # 프로젝트 관리 방법론 (프로젝트 관리 방식)
    univ_id: int
    wizard: int # 프로젝트 Setup Wizard의 완료 여부를 기록
    prof_id: int # 담당 교수의 교번


class ProjectEdit(BaseModel):  
    """프로젝트 수정 클래스"""
    pid: int  # 프로젝트의 고유번호
    pname: str  # 프로젝트 이름
    pdetails: str  # 프로젝트 내용
    psize: int  # 프로젝트 개발 인원
    pperiod: str  # 프로젝트 개발 기간 (예: "241012-241130")
    pmm: int  # 프로젝트 관리 방법론 (프로젝트 관리 방식)
    wizard: int # 프로젝트 Setup Wizard의 완료 여부를 기록
    prof_id: int # 담당 교수의 교번


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

class ProjectCheckUser(BaseModel):
    """프로젝트 팀원 조회 클래스"""
    pid: int

class Wizard(BaseModel):
    pid: int


# 로거 초기화
logging.basicConfig(
    level=logging.DEBUG,  # 디버깅 수준 설정
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 로그 메시지 포맷
    handlers=[
        logging.StreamHandler(),  # 콘솔 출력 핸들러
        logging.FileHandler("app.log", encoding="utf-8"),  # 파일 출력 핸들러
    ],
)

# logger 객체 생성
logger = logging.getLogger("project_logger")  # 로거 이름 설정

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
        logger.debug("Step 1: Generating Project UID")
        PUID = gen_project_uid()
        logger.debug(f"Generated PUID: {PUID}")
        
        logger.debug("Step 2: Initializing project in the database")
        db_result = project_DB.init_project(payload, PUID)
        if not db_result:
            logger.error(f"Database initialization failed for PUID: {PUID}")
            raise HTTPException(
                status_code=500,
                detail=f"Database initialization returned False for PUID: {PUID}",
            )
        
        logger.debug("Step 3: Initializing file system")
        file_result = init_file_system(PUID)
        if not file_result:
            logger.error(f"File system initialization failed for PUID: {PUID}")
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
        
        logger.debug("Step 4: Adding project leader to database")
        adduser_result = project_DB.add_project_user(PUID, payload.univ_id, 1, "Project Leader")
        if not adduser_result:
            logger.error(f"Add User to Project failed for PUID: {PUID}")
            raise HTTPException(
                status_code=500,
                detail=f"Add User to Project failed for PUID: {PUID}",
            )
        
        logger.debug("Step 5: Adding leader permissions")
        addleader_result = permission.add_leader_permission(PUID, payload.univ_id)
        if not addleader_result:
            logger.error(f"Add leader permission failed for PUID: {PUID}")
            raise HTTPException(
                status_code=500,
                detail=f"Add leader permission to user failed for PUID: {PUID}",
            )

        logger.debug("Step 6: Init WBS data")
        wbs_data = [["", "", "", "", "", "", "INITWBS", "", 0, "2025-01-01", "2025-01-10", 1, 0, 0, 0]]
        initwbs_result = wbs.init_wbs(wbs_data, PUID)
        if not addleader_result:
            logger.error(f"Add leader permission failed for PUID: {PUID}")
            raise HTTPException(
                status_code=500,
                detail=f"Add leader permission to user failed for PUID: {PUID}",
            )
        
        logger.info(f"Project {PUID} created successfully")
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Project created successfully",
            "PAYLOADS": {"PUID": PUID},
        }
    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}", exc_info=True)
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
                "wizard": project["p_wizard"],
            }
            for project in project_info
        ]

        return {"RESULT_CODE": 200, "RESULT_MSG": "Projects loaded successfully", "PAYLOADS": payloads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during project load: {str(e)}")


@router.post("/project/delete")
async def api_project_delete(payload: ProjectDelete):
    """프로젝트 삭제"""
    # 존재하지 않는 PID 번호로 프로젝트를 삭제하려고 시도해도 Project deleted successfully가 나오는 문제가 존재
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
        result = project_DB.edit_project_user(payload.univ_id, payload.pid, payload.role)
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
async def api_project_check_user(payload: ProjectCheckUser):
    """
    프로젝트 참여자 확인
    """
    try:
        # 프로젝트 참여자 목록 가져오기
        users = project_DB.fetch_project_user(payload.pid)
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
                "name": user["s_name"],
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


@router.post("/project/endwizard")
async def api_complete_wizard(payload: Wizard):
    try:
        result = project_DB.complete_setup_wizard(payload.pid)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to complete wizard: {e}")
    return {"RESULT_CODE": 200, "RESULT_MSG": "Wizard complete successfully"}