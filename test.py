"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : test.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2024/10/31
   업데이트 : 2024/10/31                                                      
                                                                             
   설명     : Frontend Axios에서 API 통신 테스트를 위한 라우터
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()

@router.get("/test/get")
async def test_get():
    return {"RESULT_CODE": 200,
            "RESULT_MSG": "Success",
            "PAYLOADS": {
                            "Message": "Hi there!"
                        }}

@router.post("/test/post")
async def test_post(request: Request):
    data: Dict[str, Any] = await request.json()
    return {"received_data": data}