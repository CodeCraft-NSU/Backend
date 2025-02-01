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
import traceback

router = APIRouter()

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import csv_DB
import push

class ccp_payload(BaseModel):
    pid: int = None
    univ_id: int = None
    msg: str = None

def handle_db_result(result):
    if isinstance(result, Exception):
        logging.error(f"Database error: {result}")
        return False
    return result

def create_project_info():
    return

async def pull_storage_server(pid: int, output_path: str):
    b_server_url = f"http://192.168.50.84:10080/api/ccp/push"
    async with httpx.AsyncClient() as client:
        try:
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
            else:
                logging.error(f"Failed to download from storage server. Status code: {response.status_code}")
                return {"RESULT_CODE": 500, "RESULT_MSG": f"Failed to download from storage server. Status code: {response.status_code}"}
        except Exception as e:
            logging.error(f"Error while pulling from storage server for project {pid}: {str(e)}")
            return {"RESULT_CODE": 500, "RESULT_MSG": f"Error while pulling from storage server: {str(e)}"}

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
        logging.error(f"Error occurred during encryption process for pid {pid}: {e}")
        return False

def decrypt_ccp_file(pid):
    try:
        input_file_path = f'/data/ccp/{pid}.ccp'
        output_dir = f'/data/ccp/{pid}/'

        if not os.path.exists(input_file_path):
            raise Exception(f"ccp file {input_file_path} does not exist")

        # 파일 열기
        with open(input_file_path, 'rb') as encrypted_file:
            # 헤더 읽기 (파일 개수 + 각 파일의 메타데이터)
            header = encrypted_file.read(4)
            if len(header) < 4:
                raise Exception(f"Failed to read header, insufficient data. Read {len(header)} bytes")

            num_files = struct.unpack('!I', header)[0]  # 파일 개수

            # 디렉터리 생성
            os.makedirs(output_dir, exist_ok=True)
            os.makedirs(os.path.join(output_dir, 'DATABASE'), exist_ok=True)  # DATABASE 폴더 생성
            os.makedirs(os.path.join(output_dir, 'OUTPUT'), exist_ok=True)  # OUTPUT 폴더 생성

            # 각 파일의 메타데이터 읽기 및 복원
            files_metadata = []
            for _ in range(num_files):
                # 파일 이름 길이 읽기
                file_name_length_data = encrypted_file.read(4)
                if len(file_name_length_data) < 4:
                    raise Exception(f"Failed to read file name length, insufficient data. Read {len(file_name_length_data)} bytes")
                file_name_length = struct.unpack('!I', file_name_length_data)[0]
                
                # 파일 이름 읽기
                file_name = encrypted_file.read(file_name_length).decode('utf-8')
                
                # 파일 크기 읽기
                file_size_data = encrypted_file.read(4)
                if len(file_size_data) < 4:
                    raise Exception(f"Failed to read file size, insufficient data. Read {len(file_size_data)} bytes")
                file_size = struct.unpack('!I', file_size_data)[0]

                files_metadata.append((file_name, file_size))

            # 남은 암호화된 데이터 읽기
            encrypted_data = encrypted_file.read()

            # 복호화
            decrypted_data = cipher.decrypt(encrypted_data)

            # 복호화된 데이터 저장
            decrypted_tar_path = os.path.join(output_dir, 'ccp_decrypted.tar')
            with open(decrypted_tar_path, 'wb') as decrypted_file:
                decrypted_file.write(decrypted_data)

            # 각 파일의 데이터를 복원
            with open(decrypted_tar_path, 'rb') as decrypted_tar:
                with tarfile.open(fileobj=decrypted_tar) as tar:
                    # 타르 파일 내부의 폴더 구조를 제대로 복원하도록 설정
                    for member in tar.getmembers():
                        member_path = os.path.join(output_dir, member.name)  # 최종 경로
                        
                        # 'OUTPUT' 폴더 내부만 경로 복원
                        if member.name.startswith('OUTPUT/'):
                            member_path = os.path.join(output_dir, 'OUTPUT', os.path.relpath(member.name, 'OUTPUT'))
                        elif member.name.startswith('DATABASE/'):
                            member_path = os.path.join(output_dir, 'DATABASE', os.path.relpath(member.name, 'DATABASE'))

                        # 디렉터리 생성 및 파일 추출
                        if member.isdir():
                            os.makedirs(member_path, exist_ok=True)
                        else:
                            # 파일 추출 전 존재하는지 체크하고, 필요한 디렉터리 생성
                            os.makedirs(os.path.dirname(member_path), exist_ok=True)
                            with open(member_path, 'wb') as f:
                                f.write(tar.extractfile(member).read())

        return {"RESULT_CODE": 200, "RESULT_MSG": f"Decryption successful for project {pid}"}

    except Exception as e:
        logging.error(f"Error during decryption process for pid {pid}: {str(e)}")
        return {"RESULT_CODE": 500, "RESULT_MSG": f"Decryption failed: {str(e)}"}

@router.post("/ccp/import")
async def api_project_import(payload: ccp_payload):
    """프로젝트 불러오기"""
    try:
        logging.info(f"Attempting to decrypt project {payload.pid}.ccp file")
        decryption_result = decrypt_ccp_file(payload.pid)
        if decryption_result['RESULT_CODE'] == 200:
            logging.info(f"Project {payload.pid} successfully decrypted and extracted.")
        else:
            raise HTTPException(status_code=500, detail=f"Decryption failed: {decryption_result['RESULT_MSG']}")
        return {"RESULT_CODE": 200, "RESULT_MSG": f"Project {payload.pid} imported successfully."}
    except Exception as e:
        logging.error(f"Error occurred during project import: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during project import: {str(e)}")

@router.post("/ccp/export")
async def api_project_export(payload: ccp_payload):
    """프로젝트 추출 기능"""

    logging.info(f"Initializing folder /data/ccp/{payload.pid}")
    try:
        os.makedirs(f'/data/ccp/{payload.pid}', exist_ok=True)
        os.makedirs(f'/data/ccp/{payload.pid}/DATABASE', exist_ok=True)
        os.makedirs(f'/data/ccp/{payload.pid}/OUTPUT', exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to initialize folder for project {payload.pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize folder: {str(e)}")

    logging.info(f"Exporting the database to CSV files for project ID: {payload.pid}")
    try:
        result = csv_DB.export_csv(payload.pid, payload.univ_id, payload.msg)
    except Exception as e:
        logging.error(f"Failed to export db: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export db: {e}")
    if not handle_db_result(result):
        return {"RESULT_CODE": 500, "RESULT_MSG": "Failed to export db"}

    logging.info(f"Copying the OUTPUT files from Storage Server to /data/ccp/{payload.pid}/OUTPUT")
    try:
        result = await pull_storage_server(payload.pid, f'/data/ccp/{payload.pid}/OUTPUT')
        if result['RESULT_CODE'] != 200:
            raise HTTPException(status_code=500, detail=result['RESULT_MSG'])
    except Exception as e:
        logging.error(f"Failed to download OUTPUT files from storage server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download OUTPUT files from storage server: {str(e)}")

    logging.info(f"Encrypting /data/ccp/{payload.pid} folder to /data/ccp/{payload.pid}.ccp")
    try:
        encryption_result = encrypt_ccp_file(payload.pid)
        if not encryption_result:
            raise HTTPException(status_code=500, detail=f"Failed to encrypt project folder for pid {payload.pid}")
    except Exception as e:
        logging.error(f"Error occurred during encryption process for pid {payload.pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during encryption: {str(e)}")

    logging.info(f"Pushing /data/ccp/{payload.pid}.ccp file to Next.JS Server")
    output_path = f"/data/ccp/{payload.pid}.ccp"
    push.push_to_nextjs(output_path, f"{payload.pid}.ccp")

    logging.info(f"Deleting /data/ccp/{payload.pid} folder")
    try:
        shutil.rmtree(f'/data/ccp/{payload.pid}')
    except Exception as e:
        logging.error(f"Failed to delete folder: {str(e)}")
    
    return {"RESULT_CODE": 200, "RESULT_MSG": f"Project {payload.pid} exported successfully."}
