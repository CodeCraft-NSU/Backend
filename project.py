# 프로젝트 관련 기능
from fastapi import APIRouter

router = APIRouter()

@router.post("/project_init")
async def api_prj_init_post():
    return {}

@router.post("/project_edit")
async def api_prj_edit_post():
    return {}