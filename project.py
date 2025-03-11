"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : project.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/10/16
   업데이트 : 2025/03/08
                                                                             
   설명     : 프로젝트의 생성, 수정, 조회를 위한 API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from logger import logger
import random  # gen_project_uid 함수에서 사용
import sys, os, requests, json

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import project_DB
import account_DB
import permission
import wbs

router = APIRouter()

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
    subject: int # 과목 코드


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
    subject: int # 과목 번호


class DraftPayload(BaseModel):
    """프로젝트 임시저장 관련 클래스"""
    leader_univ_id: int # 리더(프로젝트 생성자)의 학번
    new: bool = None # 새로 만든 프로젝트인지, 아니면 수정본인지 확인하는 변수; 새로 만들고 처음 저장한다면 True로
    draft_id: int = None
    pname: str = None
    pdetails: str = None
    psize: int = None
    pperiod: str = None
    pmm: int = None
    univ_id: str = None # 팀원의 학번, 사람이 여러명이라면 ;으로 구분한다. (20100000;20102222;20103333)
    prof_id: int = None
    subject: int = None


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

class FindProf_Payload(BaseModel):
    univ_id: int

# 유틸리티 함수
def gen_project_uid():
    """프로젝트 고유 ID 생성"""
    while True:
        tmp_uid = random.randint(10000, 99999)
        if not project_DB.is_uid_exists(tmp_uid):
            return tmp_uid

def init_file_system(PUID):
    """파일 시스템 초기화"""
    load_dotenv()
    headers = {"Authorization": os.getenv('ST_KEY')}
    data = {"PUID": PUID}
    try:
        response = requests.post("http://192.168.50.84:10080/api/project/init", json=data, headers=headers)
        if response.status_code == 200:
            return True
        else:
            logger.error(f"File system initialization failed for PUID {PUID}: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to init file system failed for PUID {PUID}: {str(e)}", exc_info=True)
        return False


# API 엔드포인트
@router.post("/project/init")
async def api_project_init(payload: ProjectInit):
    """프로젝트 생성 및 초기화"""
    try:
        logger.info("------------------------------------------------------------")
        logger.info("Starting project creation process")
        logger.info("Step 1: Generating Project UID")
        PUID = gen_project_uid()
        logger.info(f"Generated PUID: {PUID}")
        logger.info("Step 2: Initializing project in the database")
        db_result = project_DB.init_project(payload, PUID)
        if not db_result:
            logger.error(f"Database initialization failed for PUID: {PUID}")
            raise HTTPException(
                status_code=500,
                detail=f"Database initialization failed for PUID: {PUID}",
            )
        logger.info("Step 3: Initializing file system")
        file_result = init_file_system(PUID)
        if not file_result:
            logger.error(f"File system initialization failed for PUID: {PUID}")
            delete_result = project_DB.delete_project(PUID)
            if not delete_result:
                logger.error(f"Cleanup failed after file system initialization failure for PUID: {PUID}")
                raise HTTPException(
                    status_code=500,
                    detail=f"File system initialization failed for PUID: {PUID}, and cleanup also failed.",
                )
            raise HTTPException(
                status_code=500,
                detail=f"File system initialization failed for PUID: {PUID}. Project deleted successfully.",
            )
        logger.info("Step 4: Adding project leader to database")
        adduser_result = project_DB.add_project_user(PUID, payload.univ_id, 1, "Project Leader")
        if not adduser_result:
            logger.error(f"Adding project leader failed for PUID: {PUID}")
            raise HTTPException(
                status_code=500,
                detail=f"Adding project leader failed for PUID: {PUID}",
            )
        logger.info("Step 5: Adding leader permissions")
        addleader_result = permission.add_leader_permission(PUID, payload.univ_id)
        if not addleader_result:
            logger.error(f"Adding leader permission failed for PUID: {PUID}")
            raise HTTPException(
                status_code=500,
                detail=f"Adding leader permission to user failed for PUID: {PUID}",
            )
        logger.info("Step 6: Initializing WBS data")
        wbs_data = [["", "", "", "", "", "", "INITWBS", "", 0, "2025-01-01", "2025-01-10", 1, 0, 0, 0]]
        initwbs_result = wbs.init_wbs(wbs_data, PUID)
        if not initwbs_result:
            logger.error(f"Initializing WBS data failed for PUID: {PUID}")
            raise HTTPException(
                status_code=500,
                detail=f"Initializing WBS data failed for PUID: {PUID}",
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
        logger.error(f"Unexpected error occurred during project creation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during project creation: {str(e)}",
        )
    finally:
        logger.info("------------------------------------------------------------")


@router.post("/project/edit")
async def api_project_edit(payload: ProjectEdit):
    """프로젝트 수정"""
    try:
        result = project_DB.edit_project(payload)
        if result is True:
            logger.info(f"Project {payload.pid} has been updated successfully")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Project updated successfully"}
        raise HTTPException(status_code=500, detail="Project update failed")
    except Exception as e:
        logger.error(f"Project {payload.pid} update failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during project update: {str(e)}")


@router.post("/project/load")
async def api_project_load(payload: ProjectLoad):
    """프로젝트 조회"""
    try:
        project_info = project_DB.fetch_project_info(payload.univ_id)
        if not project_info:
            logger.warning(f"No projects found for university ID {payload.univ_id}")
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
        logger.info(f"Projects loaded successfully for university ID {payload.univ_id}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Projects loaded successfully", "PAYLOADS": payloads}
    except Exception as e:
        logger.error(f"Project load failed for university ID {payload.univ_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during project load: {str(e)}")


@router.post("/project/delete")
async def api_project_delete(payload: ProjectDelete):
    """프로젝트 삭제"""
    # 존재하지 않는 PID 번호로 프로젝트를 삭제하려고 시도해도 Project deleted successfully가 나오는 문제가 존재
    try:
        result = project_DB.delete_project(payload.pid)
        if result is True:
            logger.info(f"Project {payload.pid} has been deleted successfully")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Project deleted successfully"}
        raise HTTPException(status_code=500, detail="Project deletion failed")
    except Exception as e:
        logger.error(f"Project {payload.pid} deletion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during project deletion: {str(e)}")


@router.post("/project/adduser")
async def api_project_add_user(payload: ProjectAddUser):
    """팀원 추가"""
    try:
        result = project_DB.add_project_user(payload.pid, payload.univ_id, 0, payload.role)
        if result is True:
            logger.info(f"User added to project {payload.pid}, Univ ID {payload.univ_id}, Role {payload.role}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "User added to project successfully"}
        raise HTTPException(status_code=500, detail="Failed to add user to project")
    except Exception as e:
        logger.error(f"Error adding user to project {payload.pid}, Univ ID {payload.univ_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during user addition: {str(e)}")


@router.post("/project/deleteuser")
async def api_project_delete_user(payload: ProjectDeleteUser):
    """팀원 삭제"""
    try:
        result = project_DB.delete_project_user(payload.pid, payload.univ_id)
        if result is True:
            logger.info(f"User removed from project {payload.pid}, Univ ID {payload.univ_id}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "User removed from project successfully"}
        raise HTTPException(status_code=500, detail="Failed to remove user from project")
    except Exception as e:
        logger.error(f"Error removing user from project {payload.pid}, Univ ID {payload.univ_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during user removal: {str(e)}")


@router.post("/project/edituser")
async def api_project_edit_user(payload: ProjectEditUser):
    """팀원 정보 수정"""
    try:
        result = project_DB.edit_project_user(payload.univ_id, payload.pid, payload.role)
        if result is True:
            logger.info(f"User role updated in project {payload.pid}, Univ ID {payload.univ_id}, New Role {payload.role}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "User updated successfully"}
        raise HTTPException(status_code=500, detail="Failed to update user")
    except Exception as e:
        logger.error(f"Error updating user in project {payload.pid}, Univ ID {payload.univ_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during user update: {str(e)}")


@router.post("/project/checkpm")
async def api_project_check_pm(payload: ProjectCheckPM):
    """PM 권한 확인"""
    try:
        has_permission = project_DB.validate_pm_permission(payload.pid, payload.univ_id)
        if has_permission:
            logger.info(f"PM permission granted for project {payload.pid}, Univ ID {payload.univ_id}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Permission granted"}
        logger.warning(f"PM permission denied for project {payload.pid}, Univ ID {payload.univ_id}")
        raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        logger.error(f"Error checking PM permission for project {payload.pid}, Univ ID {payload.univ_id}: {str(e)}", exc_info=True)
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
            logger.error(f"Database error while fetching users for project {payload.pid}: {str(users)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error fetching project users: {str(users)}")
        # 프로젝트에 참여자가 없는 경우 처리
        if not users:
            logger.warning(f"Project {payload.pid} not found or has no users")
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
        logger.info(f"Successfully retrieved users for project {payload.pid}")
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Project users retrieved successfully",
            "PAYLOADS": payloads
        }
    except Exception as e:
        logger.error(f"Error checking project users for project {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error checking project users: {str(e)}")


@router.post("/project/endwizard") # wizard의 컨셉이 변경되었으므로, 추후 tutorial 등의 이름으로 변경 혹은 폐기 가능성 有
async def api_complete_wizard(payload: Wizard):
    try:
        result = project_DB.complete_setup_wizard(payload.pid)
        logger.info(f"Wizard completed successfully for project {payload.pid}")
    except Exception as e:
        logger.error(f"Failed to complete wizard for project {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to complete wizard: {e}")
    return {"RESULT_CODE": 200, "RESULT_MSG": "Wizard complete successfully"}


def init_draft_project(univ_id):
    """프로젝트 임시 저장 초기화 함수"""
    try:
        os.makedirs(f"draft/{univ_id}", exist_ok=True)
        with open(f"draft/{univ_id}/draft_num", "w") as f: 
            f.write("0")
        project_data = {
            "draft_id": {}
        }
        version = "0"
        project_data["draft_id"][version] = {
            "leader_univ_id": 0,
            "pname": "",
            "pdetails": "",
            "psize": 0,
            "pperiod": "",
            "pmm": 0,
            "univ_id": "",
            "prof_id": 0,
            "subject": 0
        }
        with open(f"draft/{univ_id}/draft.json", "w", encoding="utf-8") as f:
            json.dump(project_data, f, indent=4)
        logger.info(f"Draft project initialized for university ID {univ_id}")
        return 0
    except Exception as e:
        logger.error(f"Error occurred during draft project initialization for university ID {univ_id}: {e}", exc_info=True)
        return False


def save_draft_json(univ_id, draft_id, payload: DraftPayload):
    """draft.json에 새로운 draft를 추가하거나 기존 draft를 수정"""
    project_file = f"draft/{univ_id}/draft.json"

    if os.path.exists(project_file):
        try:
            with open(project_file, "r", encoding="utf-8") as f:
                project_data = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in {project_file}, resetting draft data", exc_info=True)
            project_data = {"draft_id": {}}
    else:
        project_data = {"draft_id": {}}
    draft_entry = {
        "leader_univ_id": payload.leader_univ_id
    }

    if payload.pname is not None:
        draft_entry["pname"] = payload.pname
    if payload.pdetails is not None:
        draft_entry["pdetails"] = payload.pdetails
    if payload.psize is not None:
        draft_entry["psize"] = payload.psize
    if payload.pperiod is not None:
        draft_entry["pperiod"] = payload.pperiod
    if payload.pmm is not None:
        draft_entry["pmm"] = payload.pmm
    if payload.univ_id is not None:
        draft_entry["univ_id"] = payload.univ_id
    if payload.prof_id is not None:
        draft_entry["prof_id"] = payload.prof_id
    if payload.subject is not None:
        draft_entry["subject"] = payload.subject
    project_data["draft_id"][str(draft_id)] = draft_entry
    with open(project_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, indent=4, ensure_ascii=False)
    logger.info(f"Draft {draft_id} saved for university ID {univ_id}")


@router.post("/project/save_draft")
async def api_save_draft_project(payload: DraftPayload):
    """프로젝트 임시 저장 함수"""
    draft_path = f"draft/{payload.leader_univ_id}/draft_num"

    if not os.path.isdir(f"draft/{payload.leader_univ_id}"):
        id = init_draft_project(payload.leader_univ_id)
        if id is False:
            logger.error(f"Failed to initialize draft project for university ID {payload.leader_univ_id}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to init draft project")
    else:
        with open(draft_path, "r") as f: id = int(f.read().strip())
    if payload.new:
        save_draft_json(payload.leader_univ_id, id, payload)
        with open(draft_path, "w") as f: f.write(str(id + 1))
    else:
        if payload.draft_id is None:
            logger.warning(f"Draft ID is required for updating for university ID {payload.leader_univ_id}")
            raise HTTPException(status_code=400, detail="Draft ID is required for updating")
        save_draft_json(payload.leader_univ_id, payload.draft_id, payload)
    logger.info(f"Draft project saved successfully for university ID {payload.leader_univ_id}")
    return {"RESULT_CODE": 200, "RESULT_MSG": "Success"}


@router.post("/project/load_draft")
async def api_load_draft_project(payload: DraftPayload):
    """프로젝트 임시 저장 로드 함수"""
    draft_folder = f"draft/{payload.leader_univ_id}"
    draft_num_path = f"{draft_folder}/draft_num"
    draft_json_path = f"{draft_folder}/draft.json"
    if not os.path.isdir(draft_folder):
        logger.warning(f"Draft folder not found for university ID {payload.leader_univ_id}")
        raise HTTPException(status_code=404, detail="Draft folder not found")
    try:
        with open(draft_num_path, "r") as f:
            draft_num = f.read().strip()
    except FileNotFoundError:
        logger.warning(f"draft_num file not found for university ID {payload.leader_univ_id}")
        raise HTTPException(status_code=404, detail="draft_num file not found")
    try:
        with open(draft_json_path, "r", encoding="utf-8") as f:
            draft_data = json.load(f)
    except FileNotFoundError:
        logger.warning(f"draft.json file not found for university ID {payload.leader_univ_id}")
        raise HTTPException(status_code=404, detail="draft.json file not found")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in draft.json for university ID {payload.leader_univ_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Invalid JSON format in draft.json")
    logger.info(f"Draft project loaded successfully for university ID {payload.leader_univ_id}")
    return {
        "RESULT_CODE": 200,
        "RESULT_MSG": "Success",
        "draft_num": int(draft_num) - 1,
        "draft_data": draft_data
    }


@router.post("/project/del_draft")
async def api_delete_draft_project(payload: DraftPayload):
    """프로젝트 임시 저장 삭제 함수"""
    draft_folder = f"draft/{payload.leader_univ_id}"
    draft_num_path = f"{draft_folder}/draft_num"
    draft_json_path = f"{draft_folder}/draft.json"
    if not os.path.isdir(draft_folder):
        logger.warning(f"Draft folder not found for university ID {payload.leader_univ_id}")
        raise HTTPException(status_code=404, detail="Draft folder not found")

    if payload.draft_id is None:
        logger.warning(f"Draft ID is required for deletion for university ID {payload.leader_univ_id}")
        raise HTTPException(status_code=400, detail="Draft ID is required for deletion")
    try:
        with open(draft_json_path, "r", encoding="utf-8") as f:
            draft_data = json.load(f)
    except FileNotFoundError:
        logger.warning(f"draft.json file not found for university ID {payload.leader_univ_id}")
        raise HTTPException(status_code=404, detail="draft.json file not found")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in draft.json for university ID {payload.leader_univ_id}", exc_info=True)
        raise HTTPException(status_code=500, detail="Invalid JSON format in draft.json")
    draft_id_str = str(payload.draft_id)
    if draft_id_str not in draft_data.get("draft_id", {}):
        logger.warning(f"Draft ID {draft_id_str} not found for university ID {payload.leader_univ_id}")
        raise HTTPException(status_code=404, detail="Draft ID not found")
    # draft_id 오름차순 정렬
    del draft_data["draft_id"][draft_id_str]
    sorted_drafts = {str(idx): value for idx, value in enumerate(draft_data["draft_id"].values())}
    draft_data["draft_id"] = sorted_drafts
    new_draft_num = len(sorted_drafts)
    with open(draft_json_path, "w", encoding="utf-8") as f:
        json.dump(draft_data, f, indent=4, ensure_ascii=False)
    with open(draft_num_path, "w") as f:
        f.write(str(new_draft_num))
    logger.info(f"Draft {payload.draft_id} deleted for university ID {payload.leader_univ_id}")
    return {"RESULT_CODE": 200, "RESULT_MSG": "Draft deleted successfully"}


@router.post("/project/load_prof")
async def api_project_load_prof(payload: ProjectLoadUser):
    """프로젝트의 담당 교수를 조회"""
    try:
        result = project_DB.fetch_project_professor_name(payload.pid)
        if isinstance(result, Exception):
            logger.error(f"Error in Load professor Operation for project {payload.pid}: {str(result)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error in Load professor Operation: {str(result)}")
        logger.info(f"Professor loaded successfully for project {payload.pid}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Load Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.error(f"Unexpected error in Load professor Operation for project {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error in Load professor Operation: {str(e)}")

@router.post("/project/count_user")
async def api_project_count_student(payload: ProjectLoad):
    """프로젝트에 포함된 사람의 수를 집계"""
    try:
        result = project_DB.fetch_project_user_count(payload.univ_id)
        if isinstance(result, Exception):
            logger.error(f"Error in count user Operation for university {payload.univ_id}: {str(result)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error in count user Operation: {str(result)}")
        logger.info(f"User count retrieved successfully for university {payload.univ_id}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Count Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.error(f"Unexpected error in count user operation for university {payload.univ_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error in count user operation: {str(e)}")

@router.post("/project/find_prof")
async def api_project_find_professor(payload: FindProf_Payload):
    """자신의 학과에 속한 교수 리스트를 불러오는 기능"""
    try:
        result = account_DB.fetch_professor_list(payload.univ_id)
        if isinstance(result, Exception):
            logger.error(f"Error in find professor operation for university {payload.univ_id}: {str(result)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error in find professor operation: {str(result)}")
        logger.info(f"Professor list retrieved successfully for university {payload.univ_id}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Find Successful.", "PAYLOAD": {"Result": result}}
    except Exception as e:
        logger.error(f"Unexpected error in find professor operation for university {payload.univ_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error in find professor operation: {str(e)}")