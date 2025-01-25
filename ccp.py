"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : ccp.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2025/01/10                                                      
   업데이트 : 2025/01/25                                      
                                                                             
   설명     : 프로젝트 Import/Export API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from pydantic import BaseModel
from urllib.parse import quote
import os, sys, logging, shutil

router = APIRouter()

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import csv_DB

class ccp_payload(BaseModel):
    pid: int = None
    univ_id: int = None

def handle_db_result(result):
    if isinstance(result, Exception):
        print(f"Database error: {result}")
        return False
    return result

def encrypt_ccp_file():
    return ""

def decrypt_ccp_file():
    return ""

@router.post("/ccp/import")
async def api_project_import(payload: ccp_payload):
    """프로젝트 불러오기"""
    return {}

@router.post("/ccp/export")
async def api_project_export(payload: ccp_payload):
    """프로젝트 추출 기능"""

    logging.info(f"Initializing folder /data/ccp/{payload.pid}")
    try:
        os.mkdir(f'/data/ccp/{payload.pid}')
        os.mkdir(f'/data/ccp/{payload.pid}/DATABASE')
        os.mkdir(f'/data/ccp/{payload.pid}/OUTPUT')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize folder: {str(e)}")

    logging.info(f"Exporting the database to CSV files for project ID: {payload.pid}")
    try:
        result = csv_DB.export_csv(payload.pid)
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to export db: {e}")
    if not handle_db_result(result):
        return {"RESULT_CODE": 500, "RESULT_MSG": "Failed to export db"}

    logging.info(f"Copying the CSV files from DB Server to /data/ccp/{payload.pid}/DATABASE")
    # 구현 중 #

    logging.info(f"Copying the OUTPUT files from Storage Server to /data/ccp/{payload.pid}/OUTPUT")
    # 구현 중 #

    logging.info(f"Creating the Project_Info.json file to /data/ccp/{payload.pid}")
    # 구현 중 #

    logging.info(f"Encrypting /data/ccp/{payload.pid} folder to /data/ccp/{payload.pid}.ccp")
    # 구현 중 #

    logging.info(f"Pushing /data/ccp/{payload.pid}.ccp file to Next.JS Server")
    # 구현 중 #

    logging.info(f"Deleting /data/ccp/{payload.pid} folder")
    try:
        shutil.rmtree(f'/data/ccp/{payload.pid}')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete folder: {str(e)}")

    return {"RESULT_CODE": 200, "RESULT_MSG": f"Project Export Job for {payload.pid} has been completed successfully."}