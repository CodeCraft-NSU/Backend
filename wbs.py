"""
   CodeCraft PMS Backend Project

   파일명   : wbs.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2024/11/24                                                       
   업데이트 : 2024/11/26                                                       
                                                                              
   설명     : WBS 관련 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sys, os

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import wbs_DB

router = APIRouter()

# Pydantic 모델 정의
class WBSAddPayload(BaseModel):
    group1: str
    group2: str
    group3: str
    group4: str
    work: str
    output_file: str
    manager: str
    note: str
    ratio: float
    start_date: str
    end_date: str
    group1no: int
    group2no: int
    group3no: int
    group4no: int
    pid: int

class WBSMultipleAddPayload(BaseModel):
    wbs_data: list  # WBS 데이터를 담은 이차원 배열
    pid: int

class WBSEditPayload(BaseModel):
    progress_no: int
    group1: str
    group2: str
    group3: str
    group4: str
    work: str
    output_file: str
    manager: str
    note: str
    ratio: float
    start_date: str
    end_date: str
    group1no: int
    group2no: int
    group3no: int
    group4no: int

class WBSDeletePayload(BaseModel):
    progress_no: int

class WBSDeleteAllPayload(BaseModel):
    pid: int

class WBSFetchPayload(BaseModel):
    pid: int

# 엔드포인트 정의
@router.post("/wbs/add_one")
async def add_one_wbs(payload: WBSAddPayload):
    try:
        result = wbs_DB.add_one_wbs(
            group1=payload.group1,
            group2=payload.group2,
            group3=payload.group3,
            group4=payload.group4,
            work=payload.work,
            output_file=payload.output_file,
            manager=payload.manager,
            note=payload.note,
            ratio=payload.ratio,
            start_date=payload.start_date,
            end_date=payload.end_date,
            group1no=payload.group1no,
            group2no=payload.group2no,
            group3no=payload.group3no,
            group4no=payload.group4no,
            pid=payload.pid,
        )
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "WBS item added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add WBS item")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding WBS item: {str(e)}")


@router.post("/wbs/add_multiple")
async def add_multiple_wbs(payload: WBSMultipleAddPayload):
    try:
        result = wbs_DB.add_multiple_wbs(payload.wbs_data, payload.pid)
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Multiple WBS items added successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to add multiple WBS items")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding multiple WBS items: {str(e)}")


@router.post("/wbs/edit")
async def edit_one_wbs(payload: WBSEditPayload):
    try:
        result = wbs_DB.edit_one_wbs(
            group1=payload.group1,
            group2=payload.group2,
            group3=payload.group3,
            group4=payload.group4,
            work=payload.work,
            output_file=payload.output_file,
            manager=payload.manager,
            note=payload.note,
            ratio=payload.ratio,
            start_date=payload.start_date,
            end_date=payload.end_date,
            group1no=payload.group1no,
            group2no=payload.group2no,
            group3no=payload.group3no,
            group4no=payload.group4no,
            progress_no=payload.progress_no,
        )
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "WBS item updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update WBS item")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating WBS item: {str(e)}")


@router.post("/wbs/delete_one")
async def delete_one_wbs(payload: WBSDeletePayload):
    try:
        result = wbs_DB.delete_one_wbs(payload.progress_no)
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "WBS item deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete WBS item")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting WBS item: {str(e)}")


@router.post("/wbs/delete_all")
async def delete_all_wbs(payload: WBSDeleteAllPayload):
    try:
        result = wbs_DB.delete_all_wbs(payload.pid)
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "All WBS items deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete all WBS items")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting all WBS items: {str(e)}")


@router.post("/wbs/fetch_all")
async def fetch_all_wbs(payload: WBSFetchPayload):
    try:
        wbs_items = wbs_DB.fetch_all_wbs(payload.pid)
        if wbs_items:
            return {"RESULT_CODE": 200, "RESULT_MSG": "WBS items fetched successfully", "PAYLOADS": wbs_items}
        else:
            return {"RESULT_CODE": 404, "RESULT_MSG": "No WBS items found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching WBS items: {str(e)}")
