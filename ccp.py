"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : ccp.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2025/01/10                                                      
   업데이트 : 2025/02/05                                     
                                                                             
   설명     : 프로젝트 Import/Export API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException, File, UploadFile
from cryptography.fernet import Fernet
from pydantic import BaseModel
from dotenv import load_dotenv
from urllib.parse import quote
from logger import logger
import os, sys, logging, shutil, tarfile, io, struct, httpx, requests
import traceback

router = APIRouter()

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import csv_DB
import push

class ccp_payload(BaseModel):
    pid: int = None
    univ_id: int = None
    msg: str = None
    ver: int = None

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
            for root, dirs, files in os.walk(input_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, input_dir)
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

def build_csv_dict(pid):
    source_dir = f"/data/ccp/{pid}/DATABASE"
    target_prefix = "/var/lib/mysql/csv/"
    prefix_mapping = {
        "project_user": "project_user",
        "student": "student",
        "professor": "professor",
        "project": "project",
        "permission": "permission",
        "work": "work",
        "progress": "progress",
        "doc_rep": "doc_report",
        "doc_s": "doc_summary",
        "doc_r": "doc_require",
        "doc_m": "doc_meeting",
        "doc_t": "doc_test",
        "doc_o": "doc_other",
        "grade": "grade",
        "doc_a": "doc_attach"
    }
    csv_dict = {}
    try:
        files = os.listdir(source_dir)
    except FileNotFoundError:
        raise Exception(f"디렉터리 {source_dir} 가 존재하지 않습니다.")
    sorted_prefixes = sorted(prefix_mapping.keys(), key=lambda x: len(x), reverse=True)
    for filename in files:
        if filename.endswith(".csv"):
            for prefix in sorted_prefixes:
                if filename.startswith(prefix):
                    key = prefix_mapping[prefix]
                    csv_dict[key] = os.path.join(target_prefix, filename)
                    break
    return csv_dict

@router.post("/ccp/import")
async def api_project_import(payload: ccp_payload):
    """프로젝트 복원 기능"""

    logging.info(f"Step 1: Retrieving version history for project {payload.pid}")
    try:
        history = csv_DB.fetch_csv_history(payload.pid)
        if not history or len(history) == 0:
            raise Exception(f"No history records found for project {payload.pid}")
        highest_ver = str(int(max(record['ver'] for record in history)) + 1)
        logging.info(f"Highest version for project {payload.pid} is {highest_ver}")
        selected_version = None
        for record in history:
            if record['ver'] == payload.ver:
                selected_version = record['ver']
                break
        if selected_version is None:
            raise Exception(f"Version {payload.ver} not found in project history")
        logging.info(f"Selected version {payload.ver} found in project history")
    except Exception as e:
        logging.error(f"Failed to retrieve version history for project {payload.pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve version history: {str(e)}")

    #return {"Highest version": highest_ver, "selected version": selected_version} # 디버깅용

    logging.info(f"Step 2: Backing up current project state for project {payload.pid}")
    try:
        logging.info(f"Initializing folder /data/ccp/{payload.pid}")
        os.makedirs(f'/data/ccp/{payload.pid}', exist_ok=True)
        os.makedirs(f'/data/ccp/{payload.pid}/DATABASE', exist_ok=True)
        os.makedirs(f'/data/ccp/{payload.pid}/OUTPUT', exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to initialize folder for project {payload.pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize folder: {str(e)}")

    logging.info(f"Exporting the database to CSV files for project ID: {payload.pid}")
    try:
        result = csv_DB.export_csv(payload.pid)
    except Exception as e:
        logging.error(f"Failed to export DB during backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export DB during backup: {str(e)}")
    if not handle_db_result(result):
        raise HTTPException(status_code=500, detail="Failed to export DB during backup")

    logging.info(f"Copying the OUTPUT files from Storage Server to /data/ccp/{payload.pid}/OUTPUT for backup")
    try:
        result = await pull_storage_server(payload.pid, f'/data/ccp/{payload.pid}/OUTPUT')
        if result['RESULT_CODE'] != 200:
            raise HTTPException(status_code=500, detail=result['RESULT_MSG'])
    except Exception as e:
        logging.error(f"Failed to download OUTPUT files during backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download OUTPUT files during backup: {str(e)}")
    
    logging.info(f"Encrypting /data/ccp/{payload.pid} folder to create backup CCP file")
    try:
        encryption_result = encrypt_ccp_file(payload.pid)
        if not encryption_result:
            raise HTTPException(status_code=500, detail=f"Failed to encrypt project folder for backup, pid {payload.pid}")
    except Exception as e:
        logging.error(f"Error during encryption for backup, pid {payload.pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during encryption for backup: {str(e)}")
    
    logging.info("Saving backup record to DB history")
    try:
        backup_message = f"Revert {highest_ver} to {payload.ver}"
        payload.msg = backup_message
        backup_ver = csv_DB.insert_csv_history(payload.pid, payload.univ_id, payload.msg)
        if backup_ver is None:
            raise Exception("Failed to insert backup history record")
        logging.info(f"Backup history record inserted with version {backup_ver}")
    except Exception as e:
        logging.error(f"Failed to save backup record: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save backup record: {str(e)}")
    logging.info("Uploading backup CCP file to Storage Server")
    try:
        history = csv_DB.fetch_csv_history(payload.pid)
        version = str(max(record['ver'] for record in history))
        ccp_file_path = f"/data/ccp/{payload.pid}.ccp"
        ccp_file_name = f"{payload.pid}_{version}.ccp"
        storage_url = "http://192.168.50.84:10080/api/ccp/pull"
        logging.info(f"Reading backup CCP file: {ccp_file_path}")
        with open(ccp_file_path, "rb") as file:
            files = {"file": (ccp_file_name, file, "application/octet-stream")}
            form_data = {"pid": str(payload.pid), "name": ccp_file_name}
            logging.info(f"Sending backup CCP file to Storage Server: {storage_url}")
            response = requests.post(storage_url, files=files, data=form_data)
        if response.status_code != 200:
            logging.error(f"Failed to upload backup CCP file: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to upload backup CCP file to Storage Server")
        logging.info(f"Backup CCP file uploaded successfully: {ccp_file_name}")
    except FileNotFoundError:
        logging.error(f"Backup CCP file not found: {ccp_file_path}")
        raise HTTPException(status_code=404, detail="Backup CCP file not found")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error during backup CCP file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Request error during backup CCP file upload: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during backup CCP file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during backup CCP file upload: {str(e)}")
    logging.info(f"Deleting /data/ccp/{payload.pid} folder and backup CCP file")
    try:
        shutil.rmtree(f'/data/ccp/{payload.pid}')
        os.remove(f'/data/ccp/{payload.pid}.ccp')
    except Exception as e:
        logging.error(f"Failed to delete folder or backup CCP file for project {payload.pid}: {str(e)}")
    
    logging.info(f"Step 2: Backup completed with version {backup_ver}")
    # return {"RESULT_CODE": 200, "RESULT_MSG": f"Project {payload.pid} imported successfully with backup version {backup_ver}."}

    logging.info(f"Step 3: Downloading CCP file for selected version {payload.ver} from Storage Server")
    try:
        selected_ccp_url = "http://192.168.50.84:10080/api/ccp/push_ccp"
        params = {"pid": payload.pid, "ver": payload.ver}
        async with httpx.AsyncClient() as client:
            response = await client.post(selected_ccp_url, params=params)
            if response.status_code != 200:
                raise Exception(f"Storage server returned status {response.status_code}")
            selected_ccp_file_path = f"/data/ccp/{payload.pid}_{payload.ver}.ccp"
            with open(selected_ccp_file_path, "wb") as f:
                f.write(response.content)
        logging.info(f"CCP file downloaded successfully: {selected_ccp_file_path}")
    except Exception as e:
        logging.error(f"Step 3 failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Step 3 failed: {str(e)}")
    
    logging.info(f"Step 4: Decrypting and extracting the downloaded CCP file for project {payload.pid}")
    try:
        target_ccp_file_path = f"/data/ccp/{payload.pid}.ccp"
        os.rename(selected_ccp_file_path, target_ccp_file_path)
        result = decrypt_ccp_file(payload.pid)
        if result.get("RESULT_CODE", 500) != 200:
            raise Exception(result.get("RESULT_MSG", "Unknown error during decryption"))
        logging.info("Decryption and extraction completed successfully")
    except Exception as e:
        logging.error(f"Step 4 failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Step 4 failed: {str(e)}")

    logging.info(f"Step 5: Pushing DATABASE CSV files to DB server for project {payload.pid}")
    db_push_url = "http://192.168.50.84:70/api/ccp/push_db"
    database_dir = f"/data/ccp/{payload.pid}/DATABASE"
    if not os.path.exists(database_dir):
        raise Exception("DATABASE folder not found in extracted files")
    try:
        files_transferred = []
        for filename in os.listdir(database_dir):
            if filename.endswith(".csv"):
                file_path = os.path.join(database_dir, filename)
                with open(file_path, "rb") as f:
                    files_payload = {"file": (filename, f, "application/octet-stream")}
                    data_payload = {"pid": str(payload.pid)}
                    response = requests.post(db_push_url, files=files_payload, data=data_payload)
                    if response.status_code != 200:
                        raise Exception(f"Failed to push file {filename}: {response.text}")
                    else:
                        files_transferred.append(filename)
        logging.info(f"Successfully pushed files to DB server: {files_transferred}")
    except Exception as e:
        logging.error(f"Failed to push DATABASE CSV files to DB server for project {payload.pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to push DATABASE CSV files to DB server: {str(e)}")

    logging.info(f"Step 5.1: Restoring DATABASE CSV files for project {payload.pid}")
    try:
        csv_files = build_csv_dict(payload.pid)
        logging.info(f"CSV files to import: {csv_files}")
        import_result = csv_DB.import_csv(csv_files, payload.pid)
        if import_result is not True:
            raise Exception("DB import_csv function returned failure")
        logging.info("DATABASE CSV files restored successfully")
    except Exception as e:
        logging.error(f"Failed to restore DATABASE CSV files for project {payload.pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to restore DATABASE CSV files: {str(e)}")

    logging.info(f"Step 6: Restoring OUTPUT files for project {payload.pid}")
    try:
        output_folder = f"/data/ccp/{payload.pid}/OUTPUT"
        target_folder = os.path.join(output_folder, str(payload.pid))
        if not os.path.exists(target_folder):
            raise Exception("Expected subfolder (named as pid) not found in OUTPUT folder")
        archive_path = f"/data/ccp/{payload.pid}_output.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            for root, dirs, files in os.walk(target_folder):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, target_folder)
                    tar.add(full_path, arcname=rel_path)
        logging.info(f"Archived OUTPUT folder to {archive_path}")
        pull_output_url = "http://192.168.50.84:10080/api/ccp/pull_output"
        archive_filename = f"{payload.pid}_output.tar.gz"
        with open(archive_path, "rb") as file:
            files = {"file": (archive_filename, file, "application/gzip")}
            form_data = {"pid": str(payload.pid), "name": archive_filename}
            logging.info(f"Uploading OUTPUT archive to Storage Server: {pull_output_url}")
            response = requests.post(pull_output_url, files=files, data=form_data)
        if response.status_code != 200:
            logging.error(f"Failed to upload OUTPUT archive: {response.text}")
            raise Exception("Failed to upload OUTPUT archive to Storage Server")
        logging.info("OUTPUT files restored successfully on Storage Server")
        os.remove(archive_path)
    except Exception as e:
        logging.info(f"Any files not found.. skipped.")
        # logging.error(f"Failed to restore OUTPUT files for project {payload.pid}: {str(e)}")
        # raise HTTPException(status_code=500, detail=f"Failed to restore OUTPUT files: {str(e)}")
        
    logging.info("Project import process completed successfully")
    return {"RESULT_CODE": 200, "RESULT_MSG": f"Project {payload.pid} imported successfully."}
    # 복원 실패 시 revert 기능 추가해야 함

def initialize_folder(pid: int):
    """백업/추출을 위한 폴더를 초기화한다."""
    logging.info(f"Initializing folder /data/ccp/{pid}")
    try:
        os.makedirs(f'/data/ccp/{pid}', exist_ok=True)
        os.makedirs(f'/data/ccp/{pid}/DATABASE', exist_ok=True)
        os.makedirs(f'/data/ccp/{pid}/OUTPUT', exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to initialize folder for project {pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize folder: {str(e)}")

def export_database_csv(payload: ccp_payload):
    """DB 서버의 데이터를 CSV 파일로 내보낸다."""
    logging.info(f"Exporting the database to CSV files for project ID: {payload.pid}")
    try:
        result = csv_DB.export_csv(payload.pid)
    except Exception as e:
        logging.error(f"Failed to export DB: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export DB: {e}")
    if not handle_db_result(result):
        raise HTTPException(status_code=500, detail="Failed to export DB")
    return result

async def download_output_files(pid: int):
    """Storage 서버에서 OUTPUT 파일들을 다운로드 받아 지정 폴더에 저장한다."""
    logging.info(f"Copying the OUTPUT files from Storage Server to /data/ccp/{pid}/OUTPUT")
    try:
        result = await pull_storage_server(pid, f'/data/ccp/{pid}/OUTPUT')
        if result['RESULT_CODE'] != 200:
            raise HTTPException(status_code=500, detail=result['RESULT_MSG'])
    except Exception as e:
        logging.error(f"Failed to download OUTPUT files from Storage server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download OUTPUT files: {str(e)}")
    return result

def encrypt_project_folder(pid: int):
    """지정 폴더를 암호화하여 CCP 파일로 생성한다."""
    logging.info(f"Encrypting /data/ccp/{pid} folder to /data/ccp/{pid}.ccp")
    try:
        encryption_result = encrypt_ccp_file(pid)
        if not encryption_result:
            raise HTTPException(status_code=500, detail=f"Failed to encrypt project folder for pid {pid}")
    except Exception as e:
        logging.error(f"Error during encryption process for pid {pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during encryption: {str(e)}")
    return encryption_result

def save_history_record(payload: ccp_payload) -> int:
    """DB 서버에 히스토리 레코드를 저장한다."""
    logging.info("Saving data to MySQL database (history record)")
    ver = csv_DB.insert_csv_history(payload.pid, payload.univ_id, payload.msg)
    if ver is None:
        raise HTTPException(status_code=500, detail="Failed to insert history record")
    return ver

def upload_ccp_file(payload: ccp_payload, ver: int):
    """생성된 CCP 파일을 Storage 서버에 업로드한다."""
    logging.info("Uploading CCP file to Storage Server")
    ccp_file_path = f"/data/ccp/{payload.pid}.ccp"
    ccp_file_name = f"{payload.pid}_{ver}.ccp"
    storage_url = "http://192.168.50.84:10080/api/ccp/pull"
    try:
        logging.info(f"Reading CCP file: {ccp_file_path}")
        with open(ccp_file_path, "rb") as file:
            files = {"file": (ccp_file_name, file, "application/octet-stream")}
            form_data = {"pid": str(payload.pid), "name": ccp_file_name}
            logging.info(f"Sending CCP file to Storage Server: {storage_url}")
            response = requests.post(storage_url, files=files, data=form_data)
        if response.status_code != 200:
            logging.error(f"Failed to upload CCP file: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to upload CCP file to Storage Server")
        logging.info(f"CCP file uploaded successfully: {ccp_file_name}")
    except FileNotFoundError:
        logging.error(f"CCP file not found: {ccp_file_path}")
        raise HTTPException(status_code=404, detail="CCP file not found")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error during CCP file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Request to storage server failed: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during CCP file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during CCP file upload: {str(e)}")

def cleanup_project_folder(pid: int):
    """작업 후 생성된 폴더와 파일들을 정리한다."""
    logging.info(f"Deleting /data/ccp/{pid} folder and CCP file")
    try:
        shutil.rmtree(f'/data/ccp/{pid}')
        os.remove(f'/data/ccp/{pid}.ccp')
    except Exception as e:
        logging.error(f"Failed to delete folder or CCP file for project {pid}: {str(e)}")

@router.post("/ccp/export")
async def api_project_export(payload: ccp_payload):
    """프로젝트 추출 기능"""
    
    try:
        logging.info(f"Initializing folder /data/ccp/{payload.pid}")
        os.makedirs(f'/data/ccp/{payload.pid}', exist_ok=True)
        os.makedirs(f'/data/ccp/{payload.pid}/DATABASE', exist_ok=True)
        os.makedirs(f'/data/ccp/{payload.pid}/OUTPUT', exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to initialize folder for project {payload.pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize folder: {str(e)}")

    logging.info(f"Exporting the database to CSV files for project ID: {payload.pid}")
    try:
        result = csv_DB.export_csv(payload.pid)
    except Exception as e:
        logging.error(f"Failed to export DB during backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export DB during backup: {str(e)}")
    if not handle_db_result(result):
        raise HTTPException(status_code=500, detail="Failed to export DB during backup")

    logging.info(f"Copying the CSV files from CD to /data/ccp/{payload.pid}/DATABASE for backup")
    try:
        API_SERVER_URL = "http://192.168.50.84:70"
        url = f"{API_SERVER_URL}/api/ccp/pull_db"
        payload_dict = {"pid": payload.pid}
        result = requests.post(url, json=payload_dict)
        response_data = result.json()
        if result.status_code != 200:
            raise HTTPException(status_code=500, detail=response_data.get("message", "Unknown error"))
    except Exception as e:
        logging.error(f"Failed to download CSV files during backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download CSV files during backup: {str(e)}")

    logging.info(f"Clean up the CSV folder from CD")
    try:
        API_SERVER_URL = "http://192.168.50.84:70"
        url = f"{API_SERVER_URL}/api/ccp/clean_db"
        payload_dict = {"pid": payload.pid}
        result = requests.post(url, json=payload_dict)
        response_data = result.json()
        if result.status_code != 200:
            raise HTTPException(status_code=500, detail=response_data.get("message", "Unknown error"))
    except Exception as e:
        logging.error(f"Failed to clean up CSV folder during backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clean up CSV folder during backup: {str(e)}")

    logging.info(f"Copying the OUTPUT files from Storage Server to /data/ccp/{payload.pid}/OUTPUT for backup")
    try:
        result = await pull_storage_server(payload.pid, f'/data/ccp/{payload.pid}/OUTPUT')
        if result['RESULT_CODE'] != 200:
            raise HTTPException(status_code=500, detail=result['RESULT_MSG'])
    except Exception as e:
        logging.error(f"Failed to download OUTPUT files during backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download OUTPUT files during backup: {str(e)}")
    
    logging.info(f"Encrypting /data/ccp/{payload.pid} folder to create backup CCP file")
    try:
        encryption_result = encrypt_ccp_file(payload.pid)
        if not encryption_result:
            raise HTTPException(status_code=500, detail=f"Failed to encrypt project folder for backup, pid {payload.pid}")
    except Exception as e:
        logging.error(f"Error during encryption for backup, pid {payload.pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during encryption for backup: {str(e)}")
    
    logging.info("Saving backup record to DB history")
    try:
        backup_message = payload.msg
        payload.msg = backup_message
        backup_ver = csv_DB.insert_csv_history(payload.pid, payload.univ_id, payload.msg)
        if backup_ver is None:
            raise Exception("Failed to insert backup history record")
        logging.info(f"Backup history record inserted with version {backup_ver}")
    except Exception as e:
        logging.error(f"Failed to save backup record: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save backup record: {str(e)}")
    logging.info("Uploading backup CCP file to Storage Server")
    try:
        history = csv_DB.fetch_csv_history(payload.pid)
        version = str(max(record['ver'] for record in history))
        ccp_file_path = f"/data/ccp/{payload.pid}.ccp"
        ccp_file_name = f"{payload.pid}_{version}.ccp"
        storage_url = "http://192.168.50.84:10080/api/ccp/pull"
        logging.info(f"Reading backup CCP file: {ccp_file_path}")
        with open(ccp_file_path, "rb") as file:
            files = {"file": (ccp_file_name, file, "application/octet-stream")}
            form_data = {"pid": str(payload.pid), "name": ccp_file_name}
            logging.info(f"Sending backup CCP file to Storage Server: {storage_url}")
            response = requests.post(storage_url, files=files, data=form_data)
        if response.status_code != 200:
            logging.error(f"Failed to upload backup CCP file: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to upload backup CCP file to Storage Server")
        logging.info(f"Backup CCP file uploaded successfully: {ccp_file_name}")
    except FileNotFoundError:
        logging.error(f"Backup CCP file not found: {ccp_file_path}")
        raise HTTPException(status_code=404, detail="Backup CCP file not found")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error during backup CCP file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Request error during backup CCP file upload: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during backup CCP file upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during backup CCP file upload: {str(e)}")
    logging.info(f"Deleting /data/ccp/{payload.pid} folder and backup CCP file")
    try:
        shutil.rmtree(f'/data/ccp/{payload.pid}')
        os.remove(f'/data/ccp/{payload.pid}.ccp')
    except Exception as e:
        logging.error(f"Failed to delete folder or backup CCP file for project {payload.pid}: {str(e)}")
    return {"RESULT_CODE": 200, "RESULT_MSG": f"Project {payload.pid} exported successfully."}

@router.post("/ccp/del_history")
async def api_delete_history(payload: ccp_payload):
    try:
        result = csv_DB.delete_csv_history(payload.pid)
        if not result:
            raise HTTPException(status_code=500, detail=f"Failed to delete history for pid {payload.pid}")
    except Exception as e:
        logging.error(f"Error occurred during delete history for pid {payload.pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during process: {str(e)}")
    return {"RESULT_CODE": 200, "RESULT_MSG": result}

@router.post("/ccp/load_history")
async def api_load_history(payload: ccp_payload):
    try:
        result = csv_DB.fetch_csv_history(payload.pid)
        if not result:
            raise HTTPException(status_code=500, detail=f"Failed to load history for pid {payload.pid}")
    except Exception as e:
        logging.error(f"Error occurred during load history for pid {payload.pid}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during load: {str(e)}")
    return {"RESULT_CODE": 200, "RESULT_MSG": result}