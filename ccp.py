"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : ccp.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2025/01/10                                                      
   업데이트 : 2025/01/25                                      
                                                                             
   설명     : 프로젝트 Import/Export API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from cryptography.fernet import Fernet
from pydantic import BaseModel
from dotenv import load_dotenv
from urllib.parse import quote
import os, sys, logging, shutil, tarfile, io, struct, httpx

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

async def pull_storage_server(pid: int, output_path: str):
    b_server_url = f"http://192.168.50.84:10080/api/ccp/push"
    async with httpx.AsyncClient() as client:
        response = await client.post(b_server_url, params={"pid": pid})
        if response.status_code == 200:
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            archive_path = os.path.join(output_path, f"{pid}_output.tar.gz")
            with open(archive_path, 'wb') as f:
                f.write(response.content)
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=output_path)
            os.remove(archive_path)
            return {"RESULT_CODE": 200, "RESULT_MSG": f"Files for project {pid} downloaded successfully."}
        else: return {"RESULT_CODE": 500, "RESULT_MSG": f"Failed to download from storage server. Status code: {response.status_code}"}

load_dotenv()

key = os.getenv('CCP_KEY')
cipher = Fernet(key)

def encrypt_ccp_file(pid):
    try:
        input_dir = f'/data/ccp/{pid}/'
        output_dir = f'/data/ccp/'

        # 파일을 tar로 압축할 메모리 버퍼 생성
        compressed_file = io.BytesIO()

        # tar 파일로 압축
        with tarfile.open(fileobj=compressed_file, mode='w|') as tar:
            # 디렉터리 내 모든 파일과 서브디렉토리 탐색
            for root, dirs, files in os.walk(input_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, input_dir)  # 상대 경로로 저장
                    tar.add(file_path, arcname=arcname)

        # 압축된 데이터 가져오기
        compressed_file.seek(0)
        compressed_data = compressed_file.read()

        # 파일 데이터 암호화
        encrypted_data = cipher.encrypt(compressed_data)

        # 헤더 작성
        num_files = len(os.listdir(input_dir))  # 디렉터리 내 파일 개수
        header = struct.pack('!I', num_files)  # 파일 개수 (4바이트)

        # 각 파일의 메타데이터 기록
        for file in os.listdir(input_dir):
            file_path = os.path.join(input_dir, file)
            file_size = os.path.getsize(file_path)
            file_name_length = len(file)
            header += struct.pack('!I', file_name_length)  # 파일 이름 길이 (4바이트)
            header += file.encode('utf-8')  # 파일 이름 (UTF-8)
            header += struct.pack('!I', file_size)  # 파일 크기 (4바이트)

        # 암호화된 ccp 파일 저장
        encrypted_file_path = os.path.join(output_dir, f'{pid}.ccp')
        with open(encrypted_file_path, 'wb') as encrypted_file:
            encrypted_file.write(header)  # 헤더 기록
            encrypted_file.write(encrypted_data)  # 암호화된 데이터 기록

        return True

    except Exception as e:
        print(f"Error occurred during encryption process for pid {pid}: {e}")
        return False

def decrypt_ccp_file(pid):
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
    try:
        result = await pull_storage_server(payload.pid, f'/data/ccp/{payload.pid}/OUTPUT')
        if result['RESULT_CODE'] != 200:
            raise HTTPException(status_code=500, detail=result['RESULT_MSG'])
    except Exception as e:
        logging.error(f"Failed to download OUTPUT files from storage server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download OUTPUT files from storage server: {str(e)}")

    logging.info(f"Creating the Project_Info.json file to /data/ccp/{payload.pid}")
    # 구현 중 #

    logging.info(f"Encrypting /data/ccp/{payload.pid} folder to /data/ccp/{payload.pid}.ccp")
    # 구현 중 #

    logging.info(f"Pushing /data/ccp/{payload.pid}.ccp file to Next.JS Server")
    # 구현 중 #

    logging.info(f"Deleting /data/ccp/{payload.pid} folder")
    # try: 디버깅 용으로 임시 주석처리 (25.01.25)
    #     shutil.rmtree(f'/data/ccp/{payload.pid}')
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Failed to delete folder: {str(e)}")

    return {"RESULT_CODE": 200, "RESULT_MSG": f"Project Export Job for {payload.pid} has been completed successfully."}