# 프로젝트 관련 기능
from fastapi import APIRouter
import mysql_connection #MySQL 연결 기능 수행

router = APIRouter()

class init_project(BaseModel): #프로젝트 생성 클래스
    pname: str #프로젝트 이름
    pdetails: str #프로젝트 내용
    psize: int #프로젝트 개발 인원
    pperiod: str #프로젝트 개발 기간
    pmm: int #프로젝트 관리 방법론; project management methodologies

class load_project(BaseModel): #프로젝트 로드 클래스
    univ_id: int #학번으로 자신이 소유한 프로젝트를 불러옴

@router.post("/project/init")
async def api_prj_init_post(payload: init_project):
    return {}

@router.post("/project/edit")
async def api_prj_edit_post():
    return {}

@router.get("/project/load")
async def api_prj_load_get(payload: load_project):
    db_connect()  # DB에 접속
    
    # DB에서 데이터를 가져오는 쿼리 실행
    # 예시로, 가상의 함수 fetch_project_info()를 사용한다고 가정
    project_info = fetch_project_info(payload.univ_id)  # 학번을 기준으로 프로젝트 정보 조회
    
    if project_info:  # 프로젝트 정보가 존재할 경우
        pname = project_info['pname']
        psize = project_info['psize']
        pperiod = project_info['pperiod']
    else:
        raise HTTPException(status_code=404, detail="Project not found")  # 프로젝트가 없는 경우 예외 처리
        
    return {"pname": pname, 
            "psize": psize, 
            "pperiod": pperiod} #P021에 프로젝트 목표?