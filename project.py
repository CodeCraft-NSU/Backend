# 프로젝트 관련 기능
from fastapi import APIRouter

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
async def api_prj_init_post():
    return {}

@router.post("/project/edit")
async def api_prj_edit_post():
    return {}

@router.get("/project/load")
async def api_prj_load_get():
    return {}