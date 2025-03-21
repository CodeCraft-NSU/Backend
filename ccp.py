"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : ccp.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2025/01/10                                                      
   업데이트 : 2025/03/08
                                                                             
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
    """데이터베이스 결과 처리 함수"""
    if isinstance(result, Exception):
        logging.error(f"Database error: {result}", exc_info=True)
        return False
    return result

def create_project_info():
    return

async def pull_storage_server(pid: int, output_path: str):
    """Storage 서버에서 특정 프로젝트의 데이터를 다운로드 및 추출하는 함수"""
    b_server_url = f"http://192.168.50.84:10080/api/ccp/push"
    timeout = httpx.Timeout(60.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(b_server_url, params={"pid": pid})
            if response.status_code == 200:
                if not os.path.exists(output_path):
                    os.makedirs(output_path)
                archive_path = os.path.join(output_path, f"{pid}_output.tar.gz")
                with open(archive_path, 'wb') as f:
                    f.write(response.content)
                logging.info(f"Downloaded archive for project {pid}: {archive_path}")
                with tarfile.open(archive_path, 'r:gz') as tar:
                    tar.extractall(path=output_path)
                os.remove(archive_path)
                logging.info(f"Extraction completed and archive removed for project {pid}")
                return {"RESULT_CODE": 200, "RESULT_MSG": f"Files for project {pid} downloaded successfully."}
            else:
                logging.error(f"Failed to download from storage server for project {pid}. Status code: {response.status_code}")
                return {"RESULT_CODE": 500, "RESULT_MSG": f"Failed to download from storage server. Status code: {response.status_code}"}
        except Exception as e:
            logging.error(f"Error while pulling from storage server for project {pid}: {str(e)}", exc_info=True)
            return {"RESULT_CODE": 500, "RESULT_MSG": f"Error while pulling from storage server: {str(e)}"}

load_dotenv()

key = os.getenv('CCP_KEY')
cipher = Fernet(key)

def encrypt_ccp_file(pid):
    """CCP 파일을 tar 압축 후 암호화하는 함수"""
    try:
        logging.info(f"------ Start encryption process for PID {pid} ------")
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
        logging.info(f"Files in {input_dir} compressed successfully.")
        # 압축된 데이터 가져오기
        compressed_file.seek(0)
        compressed_data = compressed_file.read()
        # 파일 데이터 암호화
        encrypted_data = cipher.encrypt(compressed_data)
        logging.info(f"Data encryption completed for PID {pid}.")
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
        logging.info(f"Header creation completed for PID {pid}. Number of files: {num_files}")
        # 암호화된 ccp 파일 저장
        encrypted_file_path = os.path.join(output_dir, f'{pid}.ccp')
        with open(encrypted_file_path, 'wb') as encrypted_file:
            encrypted_file.write(header)  # 헤더 기록
            encrypted_file.write(encrypted_data)  # 암호화된 데이터 기록
        logging.info(f"Encrypted CCP file saved successfully: {encrypted_file_path}")
        logging.info(f"------ End of encryption process for PID {pid} ------")
        return True
    except Exception as e:
        logging.error(f"Error occurred during encryption process for PID {pid}: {str(e)}", exc_info=True)
        return False

def decrypt_ccp_file(pid):
    """CCP 파일을 복호화하여 원본 데이터를 복원하는 함수"""
    try:
        logging.info(f"------ Start decryption process for PID {pid} ------")
        input_file_path = f'/data/ccp/{pid}.ccp'
        output_dir = f'/data/ccp/{pid}/'
        if not os.path.exists(input_file_path):
            raise Exception(f"CCP file {input_file_path} does not exist")
        logging.info(f"CCP file found: {input_file_path}")
        # 파일 열기
        with open(input_file_path, 'rb') as encrypted_file:
            # 헤더 읽기 (파일 개수 + 각 파일의 메타데이터)
            header = encrypted_file.read(4)
            if len(header) < 4:
                raise Exception(f"Failed to read header, insufficient data. Read {len(header)} bytes")
            num_files = struct.unpack('!I', header)[0]  # 파일 개수
            logging.info(f"Number of files in CCP: {num_files}")
            # 디렉터리 생성
            os.makedirs(output_dir, exist_ok=True)
            os.makedirs(os.path.join(output_dir, 'DATABASE'), exist_ok=True)
            os.makedirs(os.path.join(output_dir, 'OUTPUT'), exist_ok=True)
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
            logging.info(f"Metadata extraction completed for {num_files} files.")
            # 남은 암호화된 데이터 읽기
            encrypted_data = encrypted_file.read()
        # 복호화
        decrypted_data = cipher.decrypt(encrypted_data)
        logging.info(f"Data decryption completed for PID {pid}")
        # 복호화된 데이터 저장
        decrypted_tar_path = os.path.join(output_dir, 'ccp_decrypted.tar')
        with open(decrypted_tar_path, 'wb') as decrypted_file:
            decrypted_file.write(decrypted_data)
        logging.info(f"Decrypted tar file saved: {decrypted_tar_path}")
        # 각 파일의 데이터를 복원
        with open(decrypted_tar_path, 'rb') as decrypted_tar:
            with tarfile.open(fileobj=decrypted_tar) as tar:
                for member in tar.getmembers():
                    member_path = os.path.join(output_dir, member.name)
                    # 'OUTPUT' 폴더 내부만 경로 복원
                    if member.name.startswith('OUTPUT/'):
                        member_path = os.path.join(output_dir, 'OUTPUT', os.path.relpath(member.name, 'OUTPUT'))
                    elif member.name.startswith('DATABASE/'):
                        member_path = os.path.join(output_dir, 'DATABASE', os.path.relpath(member.name, 'DATABASE'))
                    # 디렉터리 생성 및 파일 추출
                    if member.isdir():
                        os.makedirs(member_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(member_path), exist_ok=True)
                        with open(member_path, 'wb') as f:
                            f.write(tar.extractfile(member).read())
        logging.info(f"Decryption and extraction completed for PID {pid}")
        logging.info(f"------ End of decryption process for PID {pid} ------")
        return {"RESULT_CODE": 200, "RESULT_MSG": f"Decryption successful for project {pid}"}
    except Exception as e:
        logging.error(f"Error during decryption process for PID {pid}: {str(e)}", exc_info=True)
        return {"RESULT_CODE": 500, "RESULT_MSG": f"Decryption failed: {str(e)}"}

def build_csv_dict(pid):
    """CCP 데이터베이스 폴더에서 CSV 파일을 분석하여 매핑하는 함수"""
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
        logging.info(f"------ Start building CSV dictionary for PID {pid} ------")
        if not os.path.exists(source_dir):
            raise FileNotFoundError(f"Directory {source_dir} does not exist.")
        files = os.listdir(source_dir)
        logging.info(f"Found {len(files)} files in {source_dir}.")
        sorted_prefixes = sorted(prefix_mapping.keys(), key=lambda x: len(x), reverse=True)
        for filename in files:
            if filename.endswith(".csv"):
                for prefix in sorted_prefixes:
                    if filename.startswith(prefix):
                        key = prefix_mapping[prefix]
                        csv_dict[key] = os.path.join(target_prefix, filename)
                        logging.info(f"Mapped file {filename} to key {key}.")
                        break
        logging.info(f"CSV dictionary built successfully for PID {pid}. Total mappings: {len(csv_dict)}")
        logging.info(f"------ End of CSV dictionary build for PID {pid} ------")
        return csv_dict
    except Exception as e:
        logging.error(f"Error during CSV dictionary build for PID {pid}: {str(e)}", exc_info=True)
        raise

@router.post("/ccp/import")
async def api_project_import(payload: ccp_payload):
    """프로젝트 복원 기능"""
    logging.info(f"------ Start project import process for PID {payload.pid} ------")
    try:
        # Step 1: Retrieve version history
        logging.info(f"Step 1: Retrieving version history for project {payload.pid}")
        history = csv_DB.fetch_csv_history(payload.pid)
        if not history:
            raise Exception(f"No history records found for project {payload.pid}")
        highest_ver = str(int(max(record['ver'] for record in history)) + 1)
        logging.info(f"Highest version: {highest_ver}")
        selected_version = next((record['ver'] for record in history if record['ver'] == payload.ver), None)
        if selected_version is None:
            raise Exception(f"Version {payload.ver} not found in project history")
        logging.info(f"Selected version {payload.ver} found in history")
        # Step 2: Backup current project
        logging.info(f"Step 2: Backing up current project {payload.pid}")
        os.makedirs(f'/data/ccp/{payload.pid}/DATABASE', exist_ok=True)
        os.makedirs(f'/data/ccp/{payload.pid}/OUTPUT', exist_ok=True)
        result = csv_DB.export_csv(payload.pid)
        if not handle_db_result(result):
            raise Exception("Failed to export DB during backup")
        result = await pull_storage_server(payload.pid, f'/data/ccp/{payload.pid}/OUTPUT')
        if result['RESULT_CODE'] != 200:
            raise Exception(result['RESULT_MSG'])
        if not encrypt_ccp_file(payload.pid):
            raise Exception(f"Failed to encrypt project folder for backup")
        # Step 3: Save backup history
        logging.info("Saving backup record to DB history")
        payload.msg = f"Revert {highest_ver} to {payload.ver}"
        backup_ver = csv_DB.insert_csv_history(payload.pid, payload.univ_id, payload.msg)
        if backup_ver is None:
            raise Exception("Failed to insert backup history record")
        logging.info(f"Backup history recorded as version {backup_ver}")
        # Step 4: Upload backup to Storage Server
        history = csv_DB.fetch_csv_history(payload.pid)
        version = str(max(record['ver'] for record in history))
        ccp_file_path = f"/data/ccp/{payload.pid}.ccp"
        ccp_file_name = f"{payload.pid}_{version}.ccp"
        storage_url = "http://192.168.50.84:10080/api/ccp/pull"
        logging.info(f"Uploading backup CCP file to Storage Server: {ccp_file_name}")
        with open(ccp_file_path, "rb") as file:
            files = {"file": (ccp_file_name, file, "application/octet-stream")}
            form_data = {"pid": str(payload.pid), "name": ccp_file_name}
            response = requests.post(storage_url, files=files, data=form_data)
        if response.status_code != 200:
            raise Exception("Failed to upload backup CCP file")
        # Step 5: Remove temporary backup files
        shutil.rmtree(f'/data/ccp/{payload.pid}', ignore_errors=True)
        os.remove(f'/data/ccp/{payload.pid}.ccp')
        logging.info("Backup completed and temporary files removed")
        # Step 6: Download selected CCP version
        logging.info(f"Step 6: Downloading CCP file for version {payload.ver} from Storage Server")
        selected_ccp_url = "http://192.168.50.84:10080/api/ccp/push_ccp"
        async with httpx.AsyncClient() as client:
            response = await client.post(selected_ccp_url, params={"pid": payload.pid, "ver": payload.ver})
            if response.status_code != 200:
                raise Exception(f"Storage server returned status {response.status_code}")
            selected_ccp_file_path = f"/data/ccp/{payload.pid}_{payload.ver}.ccp"
            with open(selected_ccp_file_path, "wb") as f:
                f.write(response.content)
        # Step 7: Decrypt and extract the CCP file
        logging.info("Step 7: Decrypting and extracting the downloaded CCP file")
        os.rename(selected_ccp_file_path, f"/data/ccp/{payload.pid}.ccp")
        result = decrypt_ccp_file(payload.pid)
        if result.get("RESULT_CODE", 500) != 200:
            raise Exception(result.get("RESULT_MSG", "Unknown error during decryption"))
        # Step 8: Restore DATABASE CSV files
        logging.info(f"Step 8: Pushing DATABASE CSV files to DB server for project {payload.pid}")
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
        logging.info(f"Step 8.5: Restoring DATABASE CSV files for project {payload.pid}")
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
        # Step 9: Restore OUTPUT files
        logging.info(f"Step 9: Restoring OUTPUT files for project {payload.pid}")
        output_folder = f"/data/ccp/{payload.pid}/OUTPUT"
        target_folder = os.path.join(output_folder, str(payload.pid))
        if os.path.exists(target_folder):
            archive_path = f"/data/ccp/{payload.pid}_output.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                for root, _, files in os.walk(target_folder):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, target_folder)
                        tar.add(full_path, arcname=rel_path)
            pull_output_url = "http://192.168.50.84:10080/api/ccp/pull_output"
            with open(archive_path, "rb") as file:
                response = requests.post(pull_output_url, files={"file": (f"{payload.pid}_output.tar.gz", file, "application/gzip")})
            if response.status_code != 200:
                raise Exception("Failed to upload OUTPUT archive to Storage Server")
            os.remove(archive_path)
        else:
            logging.info("No OUTPUT files found, skipping restore process.")
        logging.info(f"------ Project import process completed successfully for PID {payload.pid} ------")
        return {"RESULT_CODE": 200, "RESULT_MSG": f"Project {payload.pid} imported successfully."}
    except Exception as e:
        logging.error(f"Error during project import process for PID {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during project import: {str(e)}")
    # 복원 실패 시 revert 기능 추가해야 함

def initialize_folder(pid: int):
    """백업/추출을 위한 폴더를 초기화한다."""
    try:
        os.makedirs(f'/data/ccp/{pid}/DATABASE', exist_ok=True)
        os.makedirs(f'/data/ccp/{pid}/OUTPUT', exist_ok=True)
        logging.info(f"Folder structure initialized successfully for project {pid}")
    except Exception as e:
        logging.error(f"Failed to initialize folder for project {pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initialize folder: {str(e)}")

def export_database_csv(payload: ccp_payload):
    """DB 서버의 데이터를 CSV 파일로 내보낸다."""
    try:
        result = csv_DB.export_csv(payload.pid)
        if not handle_db_result(result):
            raise Exception("Failed to export DB")
        logging.info(f"Database export successful for project {payload.pid}")
        return result
    except Exception as e:
        logging.error(f"Failed to export database for project {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export database: {str(e)}")

async def download_output_files(pid: int):
    """Storage 서버에서 OUTPUT 파일들을 다운로드 받아 지정 폴더에 저장한다."""
    try:
        result = await pull_storage_server(pid, f'/data/ccp/{pid}/OUTPUT')
        if result['RESULT_CODE'] != 200:
            raise Exception(result['RESULT_MSG'])
        logging.info(f"OUTPUT files downloaded successfully for project {pid}")
        return result
    except Exception as e:
        logging.error(f"Failed to download OUTPUT files from Storage server for project {pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download OUTPUT files: {str(e)}")

def encrypt_project_folder(pid: int):
    """지정 폴더를 암호화하여 CCP 파일로 생성한다."""
    try:
        encryption_result = encrypt_ccp_file(pid)
        if not encryption_result:
            raise Exception(f"Failed to encrypt project folder for pid {pid}")
        logging.info(f"Encryption successful for project {pid}")
        return encryption_result
    except Exception as e:
        logging.error(f"Error during encryption process for pid {pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during encryption: {str(e)}")

def save_history_record(payload: ccp_payload) -> int:
    """DB 서버에 히스토리 레코드를 저장한다."""
    try:
        ver = csv_DB.insert_csv_history(payload.pid, payload.univ_id, payload.msg)
        if ver is None:
            raise Exception("Failed to insert history record")
        logging.info(f"History record saved successfully with version {ver} for project {payload.pid}")
        return ver
    except Exception as e:
        logging.error(f"Failed to save history record for project {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to insert history record: {str(e)}")

def upload_ccp_file(payload: ccp_payload, ver: int):
    """생성된 CCP 파일을 Storage 서버에 업로드한다."""
    logging.info(f"------ Starting CCP file upload for project {payload.pid} (version {ver}) ------")
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
            logging.error(f"Failed to upload CCP file for project {payload.pid}: {response.text}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to upload CCP file to Storage Server")
        logging.info(f"CCP file uploaded successfully: {ccp_file_name}")
        logging.info(f"------ CCP file upload completed for project {payload.pid} ------")
    except FileNotFoundError:
        logging.error(f"CCP file not found: {ccp_file_path}", exc_info=True)
        raise HTTPException(status_code=404, detail="CCP file not found")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error during CCP file upload for project {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Request to storage server failed: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during CCP file upload for project {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during CCP file upload: {str(e)}")

def cleanup_project_folder(pid: int):
    """작업 후 생성된 폴더와 파일들을 정리한다."""
    try:
        shutil.rmtree(f'/data/ccp/{pid}', ignore_errors=True)
        os.remove(f'/data/ccp/{pid}.ccp')
        logging.info(f"Cleanup completed successfully for project {pid}")
    except FileNotFoundError:
        logging.warning(f"Some files for project {pid} were not found during cleanup.")
    except Exception as e:
        logging.error(f"Failed to delete folder or CCP file for project {pid}: {str(e)}", exc_info=True)

@router.post("/ccp/export")
async def api_project_export(payload: ccp_payload):
    """프로젝트 추출 기능"""
    logging.info(f"------ Start project export process for PID {payload.pid} ------")
    # Step 1: 폴더 초기화
    try:
        logging.info(f"Initializing folder structure for project {payload.pid}")
        os.makedirs(f'/data/ccp/{payload.pid}/DATABASE', exist_ok=True)
        os.makedirs(f'/data/ccp/{payload.pid}/OUTPUT', exist_ok=True)
    except Exception as e:
        logging.error(f"Failed to initialize folder for project {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initialize folder: {str(e)}")
    # Step 2: 데이터베이스 내보내기
    try:
        logging.info(f"Exporting database to CSV for project {payload.pid}")
        result = csv_DB.export_csv(payload.pid)
        if not handle_db_result(result):
            raise Exception("Failed to export database")
        logging.info("Database exported successfully")
    except Exception as e:
        logging.error(f"Failed to export database for project {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export database: {str(e)}")
    # Step 3: CSV 파일 다운로드
    try:
        logging.info("Downloading CSV files from API Server")
        api_url = "http://192.168.50.84:70/api/ccp/pull_db"
        response = requests.post(api_url, json={"pid": payload.pid})
        if response.status_code != 200:
            raise Exception(response.json().get("message", "Unknown error"))
        logging.info("CSV files downloaded successfully")
    except Exception as e:
        logging.error(f"Failed to download CSV files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download CSV files: {str(e)}")
    # Step 4: CSV 폴더 정리
    try:
        logging.info("Cleaning up the CSV folder from API Server")
        cleanup_url = "http://192.168.50.84:70/api/ccp/clean_db"
        response = requests.post(cleanup_url, json={"pid": payload.pid})
        if response.status_code != 200:
            raise Exception(response.json().get("message", "Unknown error"))
        logging.info("CSV folder cleaned up successfully")
    except Exception as e:
        logging.error(f"Failed to clean up CSV folder: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clean up CSV folder: {str(e)}")
    # Step 5: OUTPUT 파일 다운로드
    try:
        logging.info("Downloading OUTPUT files from Storage Server")
        result = await pull_storage_server(payload.pid, f'/data/ccp/{payload.pid}/OUTPUT')
        if result['RESULT_CODE'] != 200:
            raise Exception(result['RESULT_MSG'])
        logging.info("OUTPUT files downloaded successfully")
    except Exception as e:
        logging.error(f"Failed to download OUTPUT files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download OUTPUT files: {str(e)}")
    # Step 6: 프로젝트 폴더 암호화
    try:
        logging.info("Encrypting project folder")
        if not encrypt_ccp_file(payload.pid):
            raise Exception("Failed to encrypt project folder")
        logging.info("Project folder encrypted successfully")
    except Exception as e:
        logging.error(f"Error during encryption: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during encryption: {str(e)}")
    # Step 7: 히스토리 저장
    try:
        logging.info("Saving backup history to DB")
        backup_ver = csv_DB.insert_csv_history(payload.pid, payload.univ_id, payload.msg)
        if backup_ver is None:
            raise Exception("Failed to insert backup history record")
        logging.info(f"Backup history recorded successfully as version {backup_ver}")
    except Exception as e:
        logging.error(f"Failed to save backup history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save backup history: {str(e)}")
    # Step 8: CCP 파일 업로드
    try:
        logging.info("Uploading backup CCP file to Storage Server")
        history = csv_DB.fetch_csv_history(payload.pid)
        version = str(max(record['ver'] for record in history))
        ccp_file_path = f"/data/ccp/{payload.pid}.ccp"
        ccp_file_name = f"{payload.pid}_{version}.ccp"
        storage_url = "http://192.168.50.84:10080/api/ccp/pull"
        with open(ccp_file_path, "rb") as file:
            files = {"file": (ccp_file_name, file, "application/octet-stream")}
            response = requests.post(storage_url, files=files, data={"pid": str(payload.pid), "name": ccp_file_name})
        if response.status_code != 200:
            raise Exception("Failed to upload backup CCP file")
        logging.info(f"Backup CCP file uploaded successfully: {ccp_file_name}")
    except FileNotFoundError:
        logging.error(f"Backup CCP file not found: {ccp_file_path}", exc_info=True)
        raise HTTPException(status_code=404, detail="Backup CCP file not found")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error during CCP file upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Request error during CCP file upload: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error during CCP file upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during CCP file upload: {str(e)}")
    # Step 9: 임시 폴더 정리
    try:
        logging.info("Cleaning up temporary project folder and CCP file")
        shutil.rmtree(f'/data/ccp/{payload.pid}', ignore_errors=True)
        os.remove(f'/data/ccp/{payload.pid}.ccp')
        logging.info("Temporary files deleted successfully")
    except FileNotFoundError:
        logging.warning(f"Some files were already deleted, skipping cleanup.")
    except Exception as e:
        logging.error(f"Failed to clean up project folder: {str(e)}", exc_info=True)
    logging.info(f"------ Project export process completed successfully for PID {payload.pid} ------")
    return {"RESULT_CODE": 200, "RESULT_MSG": f"Project {payload.pid} exported successfully."}

@router.post("/ccp/del_history")
async def api_delete_history(payload: ccp_payload):
    """프로젝트 히스토리 삭제"""
    try:
        result = csv_DB.delete_csv_history(payload.pid)
        if not result:
            raise Exception(f"Failed to delete history for project {payload.pid}")
        logging.info(f"History successfully deleted for project {payload.pid}")
    except Exception as e:
        logging.error(f"Error occurred while deleting history for project {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during deletion process: {str(e)}")
    return {"RESULT_CODE": 200, "RESULT_MSG": "History deleted successfully"}

@router.post("/ccp/load_history")
async def api_load_history(payload: ccp_payload):
    """프로젝트 히스토리 로드"""
    try:
        result = csv_DB.fetch_csv_history(payload.pid)
        if not result:
            raise Exception(f"Failed to load history for project {payload.pid}")
        logging.info(f"History successfully loaded for project {payload.pid}, total records: {len(result)}")
    except Exception as e:
        logging.error(f"Error occurred while loading history for project {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during history load: {str(e)}")
    return {"RESULT_CODE": 200, "RESULT_MSG": "History loaded successfully", "PAYLOAD": result}
