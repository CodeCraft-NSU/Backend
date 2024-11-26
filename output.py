"""
    CodeCraft PMS Backend Project

    파일명   : output.py
    생성자   : 김창환

    생성일   : 2024/10/20
    업데이트 : 2024/11/24

    설명     : 산출물의 생성, 수정, 조회, 삭제, 업로드를 위한 API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
import sys, os, random, requests

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import output_DB

router = APIRouter()
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class SummaryDocumentPayload(BaseModel):
    """프로젝트 개요서 간단본 모델"""
    pname: str
    pteam: str
    psummary: str
    pstart: str
    pend: str
    prange: str
    poutcomes: str
    pid: int = None
    doc_s_no: int = None  # 추가: 수정 작업에서 사용되며, 추가 작업에서는 선택적(None)

class OverviewDocumentPayload(BaseModel):
    """프로젝트 개요서 상세본 모델"""
    poverview: str
    pteam: str
    pgoals: str
    pstart: str
    pend: str
    prange: str
    pstack: str
    pid: int = None
    doc_s_no: int = None


class DocumentDeletePayload(BaseModel):
    """산출물 삭제 모델"""
    doc_s_no: int


class DocumentFetchPayload(BaseModel):
    """산출물 조회 모델"""
    pid: int


class MeetingMinutesPayload(BaseModel):
    """회의록 모델"""
    main_agenda: str
    date_time: str
    location: str
    participants: str
    responsible_person: str
    meeting_content: str
    meeting_outcome: str
    pid: int = None
    doc_m_no: int = None


class ReqSpecPayload(BaseModel):
    """요구사항 명세서 모델"""
    feature_name: str
    description: str
    priority: int
    non_functional_requirement_name: str
    non_functional_description: str
    non_functional_priority: int
    system_item: str
    system_description: str
    pid: int = None
    doc_r_no: int = None


class TestCasePayload(BaseModel):
    """테스트 케이스 모델"""
    tcname: str
    tcstart: str
    tcend: str
    tcpass: str
    pid: int = None
    doc_t_no: int = None


class OtherDocumentPayload(BaseModel):
    """기타 산출물 모델"""
    file_unique_id: str = None
    pid: int = None


class FilePathEditPayload(BaseModel):
    """파일 경로 수정 모델"""
    file_unique_id: str
    new_file_path: str


class FileNameEditPayload(BaseModel):
    """파일 이름 수정 모델"""
    file_unique_id: str
    new_file_name: str

@router.post("/output/sum_doc_add")
async def add_summary_document(payload: SummaryDocumentPayload):
    """
    프로젝트 개요서 간단본 추가 API
    """
    try:
        document_id = output_DB.add_summary_document(
            pname=payload.pname,
            pteam=payload.pteam,
            psummary=payload.psummary,
            pstart=payload.pstart,
            pend=payload.pend,
            prange=payload.prange,
            poutcomes=payload.poutcomes,
            pid=payload.pid
        )
        return {"RESULT_CODE": 200, "RESULT_MSG": "Summary document added successfully", "PAYLOADS": {"doc_s_no": document_id}}
    except Exception as e:
        print(f"Error [add_summary_document]: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding summary document: {e}")


@router.post("/output/sum_doc_edit")
async def edit_summary_document(payload: SummaryDocumentPayload):
    """
    프로젝트 개요서 간단본 수정 API
    """
    try:
        result = output_DB.edit_summary_document(
            pname=payload.pname,
            pteam=payload.pteam,
            psummary=payload.psummary,
            pstart=payload.pstart,
            pend=payload.pend,
            prange=payload.prange,
            poutcomes=payload.poutcomes,
            doc_s_no=payload.doc_s_no
        )
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Summary document updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update summary document")
    except Exception as e:
        print(f"Error [edit_summary_document]: {e}")
        raise HTTPException(status_code=500, detail=f"Error editing summary document: {e}")


@router.post("/output/sum_doc_delete")
async def delete_summary_document(payload: DocumentDeletePayload):
    """
    프로젝트 개요서 간단본 삭제 API
    """
    try:
        result = output_DB.delete_summary_document(payload.doc_s_no)
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Summary document deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete summary document")
    except Exception as e:
        print(f"Error [delete_summary_document]: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting summary document: {e}")


@router.post("/output/sum_doc_fetch")
async def fetch_all_summary_documents(payload: DocumentFetchPayload):
    """
    프로젝트 개요서 간단본 조회 API
    """
    try:
        documents = output_DB.fetch_all_summary_documents(payload.pid)
        return {"RESULT_CODE": 200, "RESULT_MSG": "Summary documents fetched successfully", "PAYLOADS": documents}
    except Exception as e:
        print(f"Error [fetch_all_summary_documents]: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching summary documents: {e}")


@router.post("/output/ovr_doc_add")
async def add_overview_document(payload: OverviewDocumentPayload):
    """
    프로젝트 개요서 상세본 추가 API
    """
    try:
        document_id = output_DB.add_overview_document(**payload.dict())
        return {"RESULT_CODE": 200, "RESULT_MSG": "Overview document added successfully", "PAYLOADS": {"doc_s_no": document_id}}
    except Exception as e:
        print(f"Error [add_overview_document]: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding overview document: {e}")


@router.post("/output/ovr_doc_edit")
async def edit_overview_document(payload: OverviewDocumentPayload):
    """
    프로젝트 개요서 상세본 수정 API
    """
    try:
        result = output_DB.edit_overview_document(
            poverview=payload.poverview,
            pteam=payload.pteam,
            pgoals=payload.pgoals,
            pstart=payload.pstart,
            pend=payload.pend,
            prange=payload.prange,
            pstack=payload.pstack,
            doc_s_no=payload.doc_s_no
        )
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Overview document updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update overview document")
    except Exception as e:
        print(f"Error [edit_overview_document]: {e}")
        raise HTTPException(status_code=500, detail=f"Error editing overview document: {e}")


@router.post("/output/ovr_doc_fetch")
async def fetch_all_overview_documents(payload: DocumentFetchPayload):
    """
    프로젝트 개요서 상세본 조회 API
    """
    try:
        documents = output_DB.fetch_all_overview_documents(payload.pid)
        return {"RESULT_CODE": 200, "RESULT_MSG": "Overview documents fetched successfully", "PAYLOADS": documents}
    except Exception as e:
        print(f"Error [fetch_all_overview_documents]: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching overview documents: {e}")


@router.post("/output/sum_doc_fetch_one")
async def fetch_one_summary_document(payload: DocumentDeletePayload):
    """
    특정 프로젝트 개요서 간단본 조회 API
    """
    try:
        document = output_DB.fetch_one_summary_document(payload.doc_s_no)
        if document:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Summary document fetched successfully", "PAYLOADS": document}
        else:
            raise HTTPException(status_code=404, detail="Summary document not found")
    except Exception as e:
        print(f"Error [fetch_one_summary_document]: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching summary document: {e}")

@router.post("/output/mm_add")
async def add_mm_document(payload: MeetingMinutesPayload):
    """
    회의록 추가 API
    """
    try:
        result = output_DB.add_meeting_minutes(
            main_agenda=payload.main_agenda,
            date_time=payload.date_time,
            location=payload.location,
            participants=payload.participants,
            responsible_person=payload.responsible_person,
            meeting_content=payload.meeting_content,
            meeting_outcome=payload.meeting_outcome,
            pid=payload.pid
        )
        return {"RESULT_CODE": 200, "RESULT_MSG": "MM document added successfully", "PAYLOADS": {"doc_m_no": result}}
    except Exception as e:
        print(f"Error [add_mm_document]: {e}")
        raise HTTPException(status_code=500, detail=f"Error add mm document: {e}")

@router.post("/output/mm_edit")
async def edit_mm_document(payload: MeetingMinutesPayload):
    """
    회의록 수정 API
    """
    try:
        result = output_DB.edit_meeting_minutes(
            main_agenda=payload.main_agenda,
            date_time=payload.date_time,
            location=payload.location,
            participants=payload.participants,
            responsible_person=payload.responsible_person,
            meeting_content=payload.meeting_content,
            meeting_outcome=payload.meeting_outcome,
            doc_m_no=payload.doc_m_no
        )
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "MM document edit successfully"}
        else:
            return {"RESULT_CODE": 500, "RESULT_MSG": "MM document edit failed"}
    except Exception as e:
        print(f"Error [add_mm_document]: {e}")
        raise HTTPException(status_code=500, detail=f"Error edit mm document: {e}")


@router.post("/output/mm_delete")
async def delete_mm_document(payload: DocumentDeletePayload):
    """
    회의록 삭제 API
    """
    try:
        result = output_DB.delete_meeting_minutes(payload.doc_s_no)
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "MM document deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete MM document")
    except Exception as e:
        print(f"Error [delete_summary_document]: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting MM document: {e}")


@router.post("/output/mm_fetch_one")
async def fetch_one_meeting_minutes(payload: DocumentDeletePayload):
    """
    특정 회의록 조회 API
    """
    try:
        meeting = output_DB.fetch_one_meeting_minutes(payload.doc_s_no)
        if meeting:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Meeting minutes fetched successfully", "PAYLOADS": meeting}
        else:
            raise HTTPException(status_code=404, detail="Meeting minutes not found")
    except Exception as e:
        print(f"Error [fetch_one_meeting_minutes]: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching meeting minutes: {e}")

@router.post("/output/mm_fetch")
async def fetch_all_meeting_minutes(payload: DocumentFetchPayload):
    """
    회의록 조회 API
    """
    try:
        documents = output_DB.fetch_all_meeting_minutes(payload.pid)
        return {"RESULT_CODE": 200, "RESULT_MSG": "MM documents fetched successfully", "PAYLOADS": documents}
    except Exception as e:
        print(f"Error [fetch_all_MM_documents]: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching MM documents: {e}")

@router.post("/output/reqspec_add")
async def add_reqspec(payload: ReqSpecPayload):
    """
    요구사항 명세서 추가 API
    """
    try:
        result = output_DB.add_reqspec(
            feature_name=payload.feature_name,
            description=payload.description,
            priority=payload.priority,
            non_functional_requirement_name=payload.non_functional_requirement_name,
            non_functional_description=payload.non_functional_description,
            non_functional_priority=payload.non_functional_priority,
            system_item=payload.system_item,
            system_description=payload.system_description,
            pid=payload.pid
        )
        return {"RESULT_CODE": 200, "RESULT_MSG": "ReqSpec document added successfully", "PAYLOADS": {"doc_r_no": result}}
    except Exception as e:
        print(f"Error [add_reqspec]: {e}")
        raise HTTPException(status_code=500, detail=f"Error add ReqSpec document: {e}")


@router.post("/output/reqspec_edit")
async def edit_reqspec(payload: ReqSpecPayload):
    """
    요구사항 명세서 수정 API
    """
    try:
        result = output_DB.edit_reqspec(
            feature_name=payload.feature_name,
            description=payload.description,
            priority=payload.priority,
            non_functional_requirement_name=payload.non_functional_requirement_name,
            non_functional_description=payload.non_functional_description,
            non_functional_priority=payload.non_functional_priority,
            system_item=payload.system_item,
            system_description=payload.system_description,
            doc_r_no=payload.doc_r_no
        )
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Requirement specification updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update requirement specification")
    except Exception as e:
        print(f"Error [edit_reqspec]: {e}")
        raise HTTPException(status_code=500, detail=f"Error editing requirement specification: {e}")


@router.post("/output/reqspec_fetch_all")
async def fetch_all_reqspec(payload: DocumentFetchPayload):
    """
    요구사항 명세서 조회 API
    """
    try:
        documents = output_DB.fetch_all_reqspec(payload.pid)
        return {"RESULT_CODE": 200, "RESULT_MSG": "Requirement specifications fetched successfully", "PAYLOADS": documents}
    except Exception as e:
        print(f"Error [fetch_all_reqspec]: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching requirement specifications: {e}")


@router.post("/output/reqspec_delete")
async def delete_reqspec(payload: DocumentDeletePayload):
    """
    요구사항 명세서 삭제 API
    """
    try:
        result = output_DB.delete_reqspec(payload.doc_s_no)
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Requirement specification deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete requirement specification")
    except Exception as e:
        print(f"Error [delete_reqspec]: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting requirement specification: {e}")

@router.post("/output/testcase_add")
async def add_testcase(payload: TestCasePayload):
    """
    테스트 케이스 추가 API
    """
    try:
        result = output_DB.add_testcase(
            tcname=payload.tcname,
            tcstart=payload.tcstart,
            tcend=payload.tcend,
            tcpass=payload.tcpass,
            pid=payload.pid
        )
        return {"RESULT_CODE": 200, "RESULT_MSG": "test case document added successfully", "PAYLOADS": {"doc_r_no": result}}
    except Exception as e:
        print(f"Error [add_testcase]: {e}")
        raise HTTPException(status_code=500, detail=f"Error add test case document: {e}")

@router.post("/output/testcase_edit")
async def edit_testcase(payload: TestCasePayload):
    """
    테스트 케이스 수정 API
    """
    try:
        result = output_DB.edit_testcase(
            tcname=payload.tcname,
            tcstart=payload.tcstart,
            tcend=payload.tcend,
            tcpass=payload.tcpass,
            doc_t_no=payload.doc_t_no
        )
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Test case updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update test case")
    except Exception as e:
        print(f"Error [edit_testcase]: {e}")
        raise HTTPException(status_code=500, detail=f"Error editing test case: {e}")


@router.post("/output/testcase_fetch_all")
async def fetch_all_testcase(payload: DocumentFetchPayload):
    """
    테스트 케이스 조회 API
    """
    try:
        testcases = output_DB.fetch_all_testcase(payload.pid)
        return {"RESULT_CODE": 200, "RESULT_MSG": "Test cases fetched successfully", "PAYLOADS": testcases}
    except Exception as e:
        print(f"Error [fetch_all_testcase]: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching test cases: {e}")


@router.post("/output/testcase_delete")
async def delete_testcase(payload: DocumentDeletePayload):
    """
    테스트 케이스 삭제 API
    """
    try:
        result = output_DB.delete_testcase(payload.doc_s_no)
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Test case deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete test case")
    except Exception as e:
        print(f"Error [delete_testcase]: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting test case: {e}")

def gen_file_uid():
    """파일 고유 ID 생성"""
    while True:
        tmp_uid = random.randint(1, 2_147_483_647) # 본래 9,999,999이었으나, int형 최대 범위 때문에 줄임
        if not output_DB.is_uid_exists(tmp_uid): return tmp_uid 

@router.post("/output/otherdoc_add")
async def add_other_document(
    file: UploadFile = File(...),
    pid: int = Form(...),
    univ_id: int = Form(...)
):
    """
    기타 산출물 추가 API
    """
    try:
        load_dotenv()
        headers = {"Authorization": os.getenv('ST_KEY')}
        file_unique_id = gen_file_uid()
        data = {
            "fuid": file_unique_id,
            "pid": pid,
            "userid": univ_id
        }

        # 파일 읽기
        file_content = await file.read()
        files = {"file": (file.filename, file_content, file.content_type)}

        # 외부 요청
        response = requests.post(
            "http://192.168.50.84:10080/api/output/otherdoc_add",
            files=files,
            data=data,
            headers=headers
        )

        # 응답 상태 코드 확인
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error: {response.status_code} - {response.text}"
            )

        # 응답 데이터 처리
        response_data = response.json()
        file_path = response_data.get("FILE_PATH")  # 외부 서버에서 반환된 파일 경로

        # uploaded_date 변환
        uploaded_date = response_data.get("uploaded_date")
        if uploaded_date:
            # Convert '241124-153059' to '2024-11-24 15:30:59'
            uploaded_date = datetime.strptime(uploaded_date, "%y%m%d-%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        else:
            raise HTTPException(status_code=500, detail="uploaded_date is missing in the response")

        # 메타데이터 저장
        db_result = output_DB.add_other_document(
            file_unique_id=file_unique_id,
            file_name=file.filename,
            file_path=file_path,
            file_date=uploaded_date,  # DATETIME 형식으로 변환된 값
            pid=pid
        ) # 이후 univ_id 정의 필요

        # DB 저장 실패 시 파일 삭제 처리
        if not db_result:
            os.remove(file_path)
            raise HTTPException(
                status_code=500,
                detail="File uploaded but failed to save metadata to the database."
            )

        # 성공 응답 반환
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "File uploaded and metadata saved successfully.",
            "PAYLOADS": {
                "file_unique_id": file_unique_id,
                "file_name": file.filename,
                "file_path": file_path,
            }
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during file upload and metadata saving: {str(e)}")

# 기타 산출물을 프론트로 전송하는 기능 필요
      
@router.post("/output/otherdoc_edit_path") # 실제로 사용하게 될지는 의문?
async def edit_otherdoc_path(file_unique_id: int = Form(...), new_file_path: str = Form(...)):
    """
    기타 산출물 경로 수정 API
    """
    try:
        result = output_DB.edit_file_path(
            file_unique_id=file_unique_id,
            new_file_path=new_file_path
        )
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "File path updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update file path")
    except Exception as e:
        print(f"Error [edit_file_path]: {e}")
        raise HTTPException(status_code=500, detail=f"Error editing file path: {e}")


@router.post("/output/otherdoc_edit_name")
async def edit_otherdoc_path(file_unique_id: int = Form(...), new_file_name: str = Form(...)):
    """
    기타 산출물 이름 수정 API
    """
    try:
        result = output_DB.edit_file_name(
            file_unique_id=file_unique_id,
            new_file_name=new_file_name
        )
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "File name updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update file name")
    except Exception as e:
        print(f"Error [edit_file_name]: {e}")
        raise HTTPException(status_code=500, detail=f"Error editing file name: {e}")


@router.post("/output/otherdoc_fetch_all")
async def fetch_all_otherdoc(pid: int = Form(...)):
    """
    기타 산출물 조회 API
    """
    try:
        documents = output_DB.fetch_all_other_documents(pid)
        return {"RESULT_CODE": 200, "RESULT_MSG": "Other Documents fetched successfully", "PAYLOADS": documents}
    except Exception as e:
        print(f"Error [fetch_all_other_documents]: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching Lists: {e}")


@router.post("/output/otherdoc_fetch_path") # 사용할지 의문
async def fetch_all_otherdoc(file_unique_id: int = Form(...)):
    """
    기타 산출물 경로 조회 API
    """
    try:
        documents = output_DB.fetch_file_path(file_unique_id)
        return {"RESULT_CODE": 200, "RESULT_MSG": "Other Documents fetched successfully", "PAYLOADS": documents}
    except Exception as e:
        print(f"Error [fetch_file_path]: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching Lists: {e}")


@router.post("/output/otherdoc_delete")
async def delete_other_document(file_unique_id: int = Form(...)):
    """
    기타 산출물  삭제 API
    """
    try:
        result = output_DB.delete_other_document(file_unique_id)
        if result:
            return {"RESULT_CODE": 200, "RESULT_MSG": "Other document deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete other document")
    except Exception as e:
        print(f"Error [delete_reqspec]: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting other document: {e}")
