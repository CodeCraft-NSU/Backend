# 프로젝트 관련 기능
from fastapi import APIRouter

router = APIRouter()

class init_project(BaseModel):
    pname: str # 프로젝트 이름
    pdetails: str # 프로젝트 내용
    psize: int # 프로젝트 개발 인원
    pperiod: str # 프로젝트 개발 기간
    pmm: int #프로젝트 관리 방법론; project management methodologies

@router.post("/project_init")
async def api_prj_init_post():
    return {}

@router.post("/project_edit")
async def api_prj_edit_post():
    return {}