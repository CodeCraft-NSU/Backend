"""
   CodeCraft PMS Backend Project

   파일명   : wbs.py                                                          
   생성자   : 김창환                                                         
                                                                              
   생성일   : 2024/11/24                                                       
   업데이트 : 2025/01/21                                                  
                                                                              
   설명     : WBS 관련 엔드포인트 정의
"""

"""
1. 프론트엔드 (Next.JS)에서 먼저 특정 프로젝트의 WBS를 조회한다. (PID 기준)
2. 조회해서 해당 프로젝트의 모든 WBS 정보를 불러온 뒤에 프론트에서 사용자가 수정을 한다.
3. 사용자가 저장을 누르면 먼저 DB에 저장돼있던 기존의 WBS 데이터를 전부 제거하고 (이때, 해당 PID 값을 가진 WBS 열만 삭제), 수정된 정보를 새로 저장
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sys, os

sys.path.append(os.path.abspath('/data/Database Project'))
import wbs_DB

router = APIRouter()

# Pydantic 모델 정의
class WBSUpdatePayload(BaseModel):
    wbs_data: list  # WBS 데이터를 담은 이차원 배열
    pid: int  # 프로젝트 ID

class WBSPayload(BaseModel):
    pid: int

def init_wbs(data, pid):
    try:
        init_result = wbs_DB.add_multiple_wbs(data, pid)
        if init_result != True:
            raise HTTPException(status_code=500, detail=f"Failed to add init WBS data. Error: {init_result}")
        
        return {"RESULT_CODE": 200, "RESULT_MSG": "WBS init successful"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during WBS batch update: {str(e)}")

# 기존 WBS 삭제 및 새로 추가하는 엔드포인트
@router.post("/wbs/update")
async def batch_update_wbs(payload: WBSUpdatePayload):
    try:
        # Step 1: 기존 WBS 데이터 삭제
        delete_result = wbs_DB.delete_all_wbs(payload.pid)
        if delete_result != True:
            raise HTTPException(status_code=500, detail=f"Failed to delete existing WBS data. Error: {delete_result}")
        
        # Step 2: 새로운 WBS 데이터 추가
        add_result = wbs_DB.add_multiple_wbs(payload.wbs_data, payload.pid)
        if add_result != True:
            raise HTTPException(status_code=500, detail=f"Failed to add new WBS data. Error: {add_result}")
        
        return {"RESULT_CODE": 200, "RESULT_MSG": "WBS batch update successful"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during WBS batch update: {str(e)}")

# 특정 프로젝트의 WBS 항목을 조회하는 엔드포인트
@router.post("/wbs/fetch_all")
async def fetch_all_wbs(payload: WBSPayload):
    try:
        wbs_items = wbs_DB.fetch_all_wbs(payload.pid)
        if wbs_items:
            return {"RESULT_CODE": 200, "RESULT_MSG": "WBS items fetched successfully", "PAYLOADS": wbs_items}
        else:
            return {"RESULT_CODE": 404, "RESULT_MSG": "No WBS items found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching WBS items: {str(e)}")

# 특정 프로젝트의 WBS 항목을 모두 삭제하는 엔드포인트
@router.post("/wbs/delete_all")
async def delete_all_wbs(payload: WBSPayload):
    try:
        delete_result = wbs_DB.delete_all_wbs(payload.pid)
        if delete_result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "All WBS items deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="No WBS items found to delete")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting all WBS items: {str(e)}")

# WBS의 진척률 평균을 조회하는 엔드포인트
@router.post("/wbs/load_ratio")
async def load_ratio(payload: WBSPayload):
    try:
        result = wbs_DB.fetch_wbs_ratio(payload.pid)
        return {"RESULT_CODE": 200, "RESULT_MSG": result}
    except HTTPException as e:
        return {"RESULT_CODE": 500, "RESULT_MSG": e.detail}
        raise e