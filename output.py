"""
    CodeCraft PMS Backend Project

    파일명   : output.py
    생성자   : 김창환

    생성일   : 2024/10/20
    업데이트 : 2025/03/31

    설명     : 산출물의 생성, 수정, 조회, 삭제, 업로드를 위한 API 엔드포인트 정의
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import quote
from logger import logger
from typing import List
import sys, os, random, requests, json, logging, shutil, subprocess

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import output_DB
import push

router = APIRouter()

class SummaryDocumentPayload(BaseModel):
    """프로젝트 개요서 간단본 모델"""
    pname: str
    pteam: str
    psummary: str
    pstart: str
    pend: str
    prange: str
    poutcomes: str
    add_date: str
    pid: int = None
    doc_s_no: int = None  # 추가: 수정 작업에서 사용되며, 추가 작업에서는 선택적(None)


class OverviewDocumentPayload(BaseModel):
    """프로젝트 개요서 상세본 모델"""
    pname: str
    pteam: str
    poverview: str
    poutcomes: str
    pgoals: str
    pstart: str
    pend: str
    prange: str
    pstack: str
    add_date: str
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
    main_agenda: str # 안건
    date_time: str # 일시
    location: str # 장소
    participants: str # 참석인원
    responsible_person: str # 책임자명
    meeting_content: str # 회의 내용
    meeting_outcome: str # 회의 결과
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
    add_date: str
    pid: int = None
    doc_r_no: int = None


class TestCasePayload(BaseModel):
    """테스트 케이스 모델"""
    doc_t_group1: str
    doc_t_name: str
    doc_t_start: str
    doc_t_end: str
    doc_t_pass: int
    doc_t_group1no: int


class MultipleTestCasesPayload(BaseModel):
    """여러 개의 테스트 케이스 추가 모델"""
    pid: int
    testcases: List[TestCasePayload]


class ReportPayload(BaseModel):
    """보고서 모델"""
    rname: str
    rwriter: str
    rdate: str
    pname: str
    pmember: str
    pprof: str
    presearch: str
    pdesign: str
    parch: str
    presult: str
    pconc: str
    pid: int = None
    doc_rep_no: int = None


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


class DownloadPayload(BaseModel):
    """파일 다운로드 모델"""
    file_type: int

class OtherDocDownloadPayload(BaseModel):
    """
    기타 산출물 다운로드 요청 모델
    """
    file_no: int


TEMP_DOWNLOAD_DIR = "/data/tmp"
STORAGE_API_KEY = os.getenv('ST_KEY')
STORAGE_SERVER_URL = "http://192.168.50.84:10080/api/output"


@router.post("/output/sum_doc_add")
async def add_summary_document(payload: SummaryDocumentPayload):
    """프로젝트 개요서 간단본 추가 API"""
    try:
        logger.info(f"Adding summary document for project {payload.pid}")
        document_id = output_DB.add_summary_document(
            pname=payload.pname,
            pteam=payload.pteam,
            psummary=payload.psummary,
            pstart=payload.pstart,
            pend=payload.pend,
            prange=payload.prange,
            poutcomes=payload.poutcomes,
            add_date=payload.add_date,
            pid=payload.pid
        )
        logger.info(f"Summary document added: ID = {document_id}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Summary document added successfully", "PAYLOADS": {"doc_s_no": document_id}}
    except Exception as e:
        logger.error(f"Error adding summary document for project {payload.pid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adding summary document: {e}")


@router.post("/output/sum_doc_edit")
async def edit_summary_document(payload: SummaryDocumentPayload):
    """프로젝트 개요서 간단본 수정 API"""
    try:
        logger.info(f"Editing summary document ID: {payload.doc_s_no}")
        result = output_DB.edit_summary_document(
            pname=payload.pname,
            pteam=payload.pteam,
            psummary=payload.psummary,
            pstart=payload.pstart,
            pend=payload.pend,
            prange=payload.prange,
            poutcomes=payload.poutcomes,
            add_date=payload.add_date,
            doc_s_no=payload.doc_s_no
        )
        if result:
            logger.info(f"Summary document updated successfully: ID = {payload.doc_s_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Summary document updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update summary document")
    except Exception as e:
        logger.error(f"Error editing summary document ID {payload.doc_s_no}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error editing summary document: {e}")


@router.post("/output/sum_doc_delete")
async def delete_summary_document(payload: DocumentDeletePayload):
    """프로젝트 개요서 간단본 삭제 API"""
    try:
        logger.info(f"Deleting summary document ID: {payload.doc_s_no}")
        result = output_DB.delete_summary_document(payload.doc_s_no)
        if result:
            logger.info(f"Summary document deleted: ID = {payload.doc_s_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Summary document deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete summary document")
    except Exception as e:
        logger.error(f"Error deleting summary document ID {payload.doc_s_no}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting summary document: {e}")


@router.post("/output/sum_doc_fetch")
async def fetch_all_summary_documents(payload: DocumentFetchPayload):
    """프로젝트 개요서 간단본 조회 API"""
    try:
        logger.info(f"Fetching all summary documents for project {payload.pid}")
        documents = output_DB.fetch_all_summary_documents(payload.pid)
        logger.info(f"Retrieved {len(documents)} summary documents for project {payload.pid}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Summary documents fetched successfully", "PAYLOADS": documents}
    except Exception as e:
        logger.error(f"Error fetching summary documents for project {payload.pid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching summary documents: {e}")


@router.post("/output/ovr_doc_add")
async def add_overview_document(payload: OverviewDocumentPayload):
    """프로젝트 개요서 상세본 추가 API"""
    try:
        logger.info(f"Adding overview document for project {payload.pid}")
        document_id = output_DB.add_overview_document(
            pname=payload.pname,
            pteam=payload.pteam,
            poverview=payload.poverview,
            poutcomes=payload.poutcomes,
            pgoals=payload.pgoals,
            pstart=payload.pstart,
            pend=payload.pend,
            prange=payload.prange,
            pstack=payload.pstack,
            add_date=payload.add_date,
            pid=payload.pid
        )
        logger.info(f"Overview document added: ID = {document_id}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Overview document added successfully", "PAYLOADS": {"doc_s_no": document_id}}
    except Exception as e:
        logger.error(f"Error adding overview document for project {payload.pid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error adding overview document: {e}")


@router.post("/output/ovr_doc_edit")
async def edit_overview_document(payload: OverviewDocumentPayload):
    """프로젝트 개요서 상세본 수정 API"""
    try:
        logger.info(f"Editing overview document ID: {payload.doc_s_no}")
        result = output_DB.edit_overview_document(
            pname=payload.pname,
            pteam=payload.pteam,
            poverview=payload.poverview,
            poutcomes=payload.poutcomes,
            pgoals=payload.pgoals,
            pstart=payload.pstart,
            pend=payload.pend,
            prange=payload.prange,
            pstack=payload.pstack,
            add_date=payload.add_date,
            doc_s_no=payload.doc_s_no
        )
        if result:
            logger.info(f"Overview document updated successfully: ID = {payload.doc_s_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Overview document updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update overview document")
    except Exception as e:
        logger.error(f"Error editing overview document ID {payload.doc_s_no}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error editing overview document: {e}")


@router.post("/output/ovr_doc_fetch")
async def fetch_all_overview_documents(payload: DocumentFetchPayload):
    """프로젝트 개요서 상세본 조회 API"""
    try:
        logger.info(f"Fetching all overview documents for project {payload.pid}")
        documents = output_DB.fetch_all_overview_documents(payload.pid)
        logger.info(f"Retrieved {len(documents)} overview documents for project {payload.pid}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Overview documents fetched successfully", "PAYLOADS": documents}
    except Exception as e:
        logger.error(f"Error fetching overview documents for project {payload.pid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching overview documents: {e}")


@router.post("/output/sum_doc_fetch_one")
async def fetch_one_summary_document(payload: DocumentDeletePayload):
    """특정 프로젝트 개요서 간단본 조회 API"""
    try:
        logger.info(f"Fetching summary document ID: {payload.doc_s_no}")
        document = output_DB.fetch_one_summary_document(payload.doc_s_no)
        if document:
            logger.info(f"Summary document fetched successfully: ID = {payload.doc_s_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Summary document fetched successfully", "PAYLOADS": document}
        else:
            raise HTTPException(status_code=404, detail="Summary document not found")
    except Exception as e:
        logger.error(f"Error fetching summary document ID {payload.doc_s_no}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching summary document: {e}")


@router.post("/output/mm_add")
async def add_mm_document(payload: MeetingMinutesPayload):
    """회의록 추가 API"""
    try:
        logger.info(f"Adding meeting minutes document for project {payload.pid}")
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
        logger.info(f"Meeting minutes document added successfully: ID = {result}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "MM document added successfully", "PAYLOADS": {"doc_m_no": result}}
    except Exception as e:
        logger.error(f"Error adding meeting minutes document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error add mm document: {e}")


@router.post("/output/mm_edit")
async def edit_mm_document(payload: MeetingMinutesPayload):
    """회의록 수정 API"""
    try:
        logger.info(f"Editing meeting minutes document ID: {payload.doc_m_no}")
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
            logger.info(f"Meeting minutes document updated successfully: ID = {payload.doc_m_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "MM document edit successfully"}
        else:
            logger.warning(f"Meeting minutes document edit failed: ID = {payload.doc_m_no}")
            return {"RESULT_CODE": 500, "RESULT_MSG": "MM document edit failed"}
    except Exception as e:
        logger.error(f"Error editing meeting minutes document ID {payload.doc_m_no}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error edit mm document: {e}")


@router.post("/output/mm_delete")
async def delete_mm_document(payload: DocumentDeletePayload):
    """
    회의록 삭제 API
    """
    try:
        result = output_DB.delete_meeting_minutes(payload.doc_s_no)
        if result:
            logger.debug(f"MM document deleted: doc_s_no={payload.doc_s_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "MM document deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete MM document")
    except Exception as e:
        logger.error(f"Error deleting MM document [doc_s_no={payload.doc_s_no}]: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting MM document: {e}")


@router.post("/output/mm_fetch_one")
async def fetch_one_meeting_minutes(payload: DocumentDeletePayload):
    """
    특정 회의록 조회 API
    """
    try:
        meeting = output_DB.fetch_one_meeting_minutes(payload.doc_s_no)
        if meeting:
            logger.debug(f"Fetched one MM document: doc_s_no={payload.doc_s_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Meeting minutes fetched successfully", "PAYLOADS": meeting}
        else:
            raise HTTPException(status_code=404, detail="Meeting minutes not found")
    except Exception as e:
        logger.error(f"Error fetching one MM document [doc_s_no={payload.doc_s_no}]: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching meeting minutes: {e}")


@router.post("/output/mm_fetch")
async def fetch_all_meeting_minutes(payload: DocumentFetchPayload):
    """
    회의록 조회 API
    """
    try:
        documents = output_DB.fetch_all_meeting_minutes(payload.pid)
        logger.debug(f"Fetched all MM documents: pid={payload.pid}, count={len(documents)}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "MM documents fetched successfully", "PAYLOADS": documents}
    except Exception as e:
        logger.error(f"Error fetching MM documents [pid={payload.pid}]: {e}")
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
            add_date=payload.add_date,
            pid=payload.pid
        )
        logger.debug(f"ReqSpec document added: pid={payload.pid}, doc_r_no={result}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "ReqSpec document added successfully", "PAYLOADS": {"doc_r_no": result}}
    except Exception as e:
        logger.error(f"Error adding ReqSpec document [pid={payload.pid}]: {e}")
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
            doc_r_date=payload.add_date,
            doc_r_no=payload.doc_r_no
        )
        if result:
            logger.debug(f"ReqSpec document updated: doc_r_no={payload.doc_r_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Requirement specification updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update requirement specification")
    except Exception as e:
        logger.error(f"Error editing ReqSpec document [doc_r_no={payload.doc_r_no}]: {e}")
        raise HTTPException(status_code=500, detail=f"Error editing requirement specification: {e}")


@router.post("/output/reqspec_fetch_all")
async def fetch_all_reqspec(payload: DocumentFetchPayload):
    """
    요구사항 명세서 조회 API
    """
    try:
        documents = output_DB.fetch_all_reqspec(payload.pid)
        logger.debug(f"Fetched {len(documents)} requirement specifications for pid={payload.pid}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Requirement specifications fetched successfully", "PAYLOADS": documents}
    except Exception as e:
        logger.error(f"Error [fetch_all_reqspec] for pid={payload.pid}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching requirement specifications: {e}")


@router.post("/output/reqspec_delete")
async def delete_reqspec(payload: DocumentDeletePayload):
    """
    요구사항 명세서 삭제 API
    """
    try:
        result = output_DB.delete_reqspec(payload.doc_s_no)
        if result:
            logger.debug(f"Requirement specification deleted: doc_s_no={payload.doc_s_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Requirement specification deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete requirement specification")
    except Exception as e:
        logger.error(f"Error [delete_reqspec] for doc_s_no={payload.doc_s_no}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting requirement specification: {e}")


def init_testcase(data, pid):
    try:
        result = output_DB.add_multiple_testcase(data, pid)
        if isinstance(result, Exception):
            logger.error(f"Failed to add initial test case data for project {pid}: {str(result)}", exc_info=True)
            raise Exception(f"Failed to add init Testcase data. Error: {str(result)}")
        logger.info(f"Project {pid} has been successfully initialized with test cases")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Testcase init successful"}
    except Exception as e:
        logger.error(f"Error occurred while initializing test cases for project {pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during Testcase batch update: {str(e)}")


@router.post("/output/testcase_update")
async def update_tastcase(payload: MultipleTestCasesPayload):
    """WBS 스타일의 TC 업데이트 API"""
    try:
        logger.info(f"Received request to update test cases for project {payload.pid}")
        delete_result = output_DB.delete_all_testcase(payload.pid)
        logger.info(f"Existing test cases deleted for project {payload.pid}")
        testcase_data = [
            [
                tc.doc_t_group1,
                tc.doc_t_name,
                tc.doc_t_start,
                tc.doc_t_end,
                tc.doc_t_pass,
                tc.doc_t_group1no
            ]
            for tc in payload.testcases
        ]
        add_result = output_DB.add_multiple_testcase(testcase_data, payload.pid)
        if add_result != True:
            logger.error(f"Failed to add new test cases for project {payload.pid}: {add_result}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to add new test cases. Error: {add_result}")
        logger.info(f"Successfully updated test cases for project {payload.pid}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Test cases updated successfully"}
    except Exception as e:
        logger.error(f"Error occurred while updating test cases for project {payload.pid}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during test case update: {str(e)}")


@router.post("/output/testcase_add") # TC 컨셉 변경으로 인한 미사용 (25.03.24)
async def add_multiple_testcase(payload: MultipleTestCasesPayload):
    """ 테스트 케이스 추가 API """
    try:
        testcase_data = [
            [
                tc.doc_t_group1,
                tc.doc_t_name,
                tc.doc_t_start,
                tc.doc_t_end,
                tc.doc_t_pass,
                tc.doc_t_group1no
            ]
            for tc in payload.testcases
        ]
        result = output_DB.add_multiple_testcase(testcase_data, payload.pid)
        if result is True:
            logger.debug(f"Added {len(testcase_data)} test cases for pid={payload.pid}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Test cases added successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Error adding test cases: {result}")
    except Exception as e:
        logger.error(f"Error [add_multiple_testcase] for pid={payload.pid}: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding test cases: {e}")


@router.post("/output/testcase_load")
async def fetch_all_testcase(payload: DocumentFetchPayload):
    """
    테스트 케이스 조회 API
    """
    try:
        testcases = output_DB.fetch_all_testcase(payload.pid)
        logger.debug(f"Fetched {len(testcases)} test cases for pid={payload.pid}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Test cases fetched successfully", "PAYLOADS": testcases}
    except Exception as e:
        logger.error(f"Error [fetch_all_testcase] for pid={payload.pid}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching test cases: {e}")


@router.post("/output/testcase_delete")
async def delete_all_testcase(payload: DocumentFetchPayload):
    """
    테스트 케이스 삭제 API
    """
    try:
        result = output_DB.delete_all_testcase(payload.pid)
        if result is True:
            logger.debug(f"Deleted all test cases for pid={payload.pid}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "All test cases deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Error deleting test cases: {result}")
    except Exception as e:
        logger.error(f"Error [delete_all_testcase] for pid={payload.pid}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting test cases: {e}")


@router.post("/output/report_add")
async def add_report(payload: ReportPayload):
    """보고서 추가 API"""
    try:
        result = output_DB.add_report(
            doc_rep_name=payload.rname,
            doc_rep_writer=payload.rwriter,
            doc_rep_date=payload.rdate,
            doc_rep_pname=payload.pname,
            doc_rep_member=payload.pmember,
            doc_rep_professor=payload.pprof,
            doc_rep_research=payload.presearch,
            doc_rep_design=payload.pdesign,
            doc_rep_arch=payload.parch,
            doc_rep_result=payload.presult,
            doc_rep_conclusion=payload.pconc,
            pid=payload.pid
        )
        logger.debug(f"Added report document for pid={payload.pid}, doc_rep_no={result}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Report document added successfully", "PAYLOADS": {"doc_rep_no": result}}
    except Exception as e:
        logger.error(f"Error [add_report] for pid={payload.pid}: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding report document: {e}")


@router.post("/output/report_edit")
async def edit_report(payload: ReportPayload):
    """
    보고서 수정 API
    """
    try:
        result = output_DB.edit_report(
            doc_rep_name=payload.rname,
            doc_rep_writer=payload.rwriter,
            doc_rep_date=payload.rdate,
            doc_rep_pname=payload.pname,
            doc_rep_member=payload.pmember,
            doc_rep_professor=payload.pprof,
            doc_rep_research=payload.presearch,
            doc_rep_design=payload.pdesign,
            doc_rep_arch=payload.parch,
            doc_rep_result=payload.presult,
            doc_rep_conclusion=payload.pconc,
            doc_rep_no=payload.doc_rep_no
        )
        if result:
            logger.debug(f"Updated report document: doc_rep_no={payload.doc_rep_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Report updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update report")
    except Exception as e:
        logger.error(f"Error [edit_report] for doc_rep_no={payload.doc_rep_no}: {e}")
        raise HTTPException(status_code=500, detail=f"Error editing report: {e}")


@router.post("/output/report_fetch_all")
async def fetch_all_report(payload: DocumentFetchPayload):
    """
    보고서 조회 API
    """
    try:
        report = output_DB.fetch_all_report(payload.pid)
        logger.debug(f"Fetched {len(report)} reports for pid={payload.pid}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Report fetched successfully", "PAYLOADS": report}
    except Exception as e:
        logger.error(f"Error [fetch_all_report] for pid={payload.pid}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching report: {e}")


@router.post("/output/report_delete")
async def delete_report(payload: DocumentDeletePayload):
    """
    보고서 삭제 API
    """
    try:
        result = output_DB.delete_report(payload.doc_s_no)
        if result:
            logger.debug(f"Deleted report document: doc_s_no={payload.doc_s_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Report deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete report")
    except Exception as e:
        logger.error(f"Error [delete_report] for doc_s_no={payload.doc_s_no}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting report: {e}")


def gen_file_uid():
    """파일 고유 ID 생성"""
    while True:
        tmp_uid = random.randint(1, 2_147_483_647)  # 본래 9,999,999이었으나, int형 최대 범위 때문에 줄임
        if not output_DB.is_uid_exists(tmp_uid):
            return tmp_uid


@router.post("/output/otherdoc_add")
async def add_other_documents(
    files: List[UploadFile] = File(...),
    pid: int = Form(...),
    univ_id: int = Form(...)
):
    """
    기타 산출물 추가 API
    """
    logger.info("------------------------------------------------------------")
    logger.info("Starting process to add other documents")
    try:
        load_dotenv()
        logger.info("Environment variables loaded successfully")
        headers = {"Authorization": os.getenv('ST_KEY')}
        attachments = []
        total_files = len(files)
        logger.info(f"Number of files to process: {total_files}")
        for idx, file in enumerate(files, start=1):
            logger.info(f"[{idx}/{total_files}] Processing file: {file.filename}")
            file_unique_id = gen_file_uid()
            logger.info(f"Generated file unique id: {file_unique_id} for file: {file.filename}")
            data = {
                "fuid": file_unique_id,
                "pid": pid,
                "userid": univ_id
            }
            file_content = await file.read()
            logger.info(f"Read {len(file_content)} bytes from file: {file.filename}")

            files_payload = {"file": (file.filename, file_content, file.content_type)}
            # 최대 3회 재시도
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info(f"Uploading file {file.filename} to storage server (Attempt {attempt})")
                    response = requests.post(
                        "http://192.168.50.84:10080/api/output/otherdoc_add",
                        files=files_payload,
                        data=data,
                        headers=headers,
                        timeout=60
                    )
                    if response.status_code == 200:
                        logger.info(f"File upload succeeded on attempt {attempt} for {file.filename}")
                        break
                    else:
                        error_msg = (f"File upload failed for {file.filename} on attempt {attempt} "
                                     f"with status code {response.status_code}: {response.text}")
                        logger.error(error_msg)
                        if attempt == max_attempts:
                            raise HTTPException(
                                status_code=response.status_code,
                                detail=error_msg
                            )
                except requests.exceptions.RequestException as req_exc:
                    logger.error(
                        f"RequestException on attempt {attempt} for file {file.filename}: {str(req_exc)}",
                        exc_info=True
                    )
                    if attempt == max_attempts:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Request failed for {file.filename} after {attempt} attempts: {str(req_exc)}"
                        )
            response_data = response.json()
            logger.info(f"Received response for file {file.filename}: {response_data}")
            file_path = response_data.get("FILE_PATH")
            uploaded_date = response_data.get("uploaded_date")
            if uploaded_date:
                try:
                    uploaded_date = datetime.strptime(uploaded_date, "%y%m%d-%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                    logger.info(f"Parsed uploaded_date for file {file.filename}: {uploaded_date}")
                except Exception as parse_error:
                    error_msg = f"Error parsing uploaded_date for {file.filename}: {str(parse_error)}"
                    logger.error(error_msg, exc_info=True)
                    raise HTTPException(status_code=500, detail=error_msg)
            else:
                error_msg = f"uploaded_date is missing in the response for {file.filename}"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
            logger.info(f"Saving metadata to database for file: {file.filename}")
            db_result = output_DB.add_other_document(
                file_unique_id=file_unique_id,
                file_name=file.filename,
                file_path=file_path,
                file_date=uploaded_date,
                univ_id=univ_id,
                pid=pid
            )
            if not db_result:
                logger.error(f"Database failed to save metadata for {file.filename}. Removing file from storage.")
                try:
                    os.remove(file_path)
                    logger.info(f"Removed file from storage: {file_path}")
                except Exception as remove_exc:
                    logger.error(f"Failed to remove file {file_path}: {str(remove_exc)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="File uploaded but failed to save metadata to the database."
                )
            logger.info(f"File processed successfully: {file.filename}")
            attachments.append({
                "file_unique_id": file_unique_id,
                "file_name": file.filename,
                "file_path": file_path,
                "file_date": uploaded_date
            })
        logger.info("All files processed successfully")
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Files uploaded and metadata saved successfully.",
            "PAYLOADS": attachments
        }
    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.error("Unexpected error occurred during file upload and metadata saving", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    finally:
        logger.info("------------------------------------------------------------")
        
      
@router.post("/output/otherdoc_edit_path")
async def edit_otherdoc_path(file_unique_id: int = Form(...), new_file_path: str = Form(...)):
    """
    기타 산출물 경로 수정 API
    """
    logger.info(f"Starting file path update for file_unique_id: {file_unique_id}")
    try:
        result = output_DB.edit_file_path(
            file_unique_id=file_unique_id,
            new_file_path=new_file_path
        )
        if result:
            logger.info(f"File path updated successfully for file_unique_id: {file_unique_id}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "File path updated successfully"}
        else:
            logger.error(f"Failed to update file path for file_unique_id: {file_unique_id}")
            raise HTTPException(status_code=500, detail="Failed to update file path")
    except Exception as e:
        logger.error(f"Error [edit_file_path] for file_unique_id {file_unique_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error editing file path: {e}")


@router.post("/output/otherdoc_edit_name")
async def edit_otherdoc_name(file_unique_id: int = Form(...), new_file_name: str = Form(...)):
    """
    기타 산출물 이름 수정 API
    """
    logger.info(f"Starting file name update for file_unique_id: {file_unique_id}")
    try:
        result = output_DB.edit_file_name(
            file_unique_id=file_unique_id,
            new_file_name=new_file_name
        )
        if result:
            logger.info(f"File name updated successfully for file_unique_id: {file_unique_id}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "File name updated successfully"}
        else:
            logger.error(f"Failed to update file name for file_unique_id: {file_unique_id}")
            raise HTTPException(status_code=500, detail="Failed to update file name")
    except Exception as e:
        logger.error(f"Error [edit_file_name] for file_unique_id {file_unique_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error editing file name: {e}")


@router.post("/output/otherdoc_fetch_all")
async def fetch_all_otherdoc(pid: int = Form(...)):
    """
    기타 산출물 조회 API
    """
    logger.info(f"Fetching all other documents for pid: {pid}")
    try:
        documents = output_DB.fetch_all_other_documents(pid)
        logger.info(f"Fetched {len(documents)} other documents for pid: {pid}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Other Documents fetched successfully", "PAYLOADS": documents}
    except Exception as e:
        logger.error(f"Error [fetch_all_other_documents] for pid {pid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {e}")


@router.post("/output/otherdoc_fetch_path")
async def fetch_all_otherdoc(payload: OtherDocDownloadPayload):
    """
    기타 산출물 경로 조회 API
    """
    logger.info(f"Fetching file path for file_no: {payload.file_no}")
    try:
        documents = output_DB.fetch_file_path(payload.file_no)
        logger.info(f"Fetched file path for file_no: {payload.file_no}")
        return {"RESULT_CODE": 200, "RESULT_MSG": "Other Documents fetched successfully", "PAYLOADS": documents}
    except Exception as e:
        logger.error(f"Error [fetch_file_path] for file_no {payload.file_no}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching file path: {e}")


@router.post("/output/otherdoc_delete")
async def delete_other_document(payload: OtherDocDownloadPayload):
    """
    기타 산출물 삭제 API
    """
    logger.info(f"Starting deletion of other document with file_no: {payload.file_no}")
    try:
        result = output_DB.delete_other_document(payload.file_no)
        if result:
            logger.info(f"Other document deleted successfully for file_no: {payload.file_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Other document deleted successfully"}
        else:
            logger.error(f"Failed to delete other document for file_no: {payload.file_no}")
            raise HTTPException(status_code=500, detail="Failed to delete other document")
    except Exception as e:
        logger.error(f"Error [delete_other_document] for file_no {payload.file_no}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting other document: {e}")


@router.post("/output/otherdoc_download")
async def api_otherdoc_download(payload: OtherDocDownloadPayload):
    """
        API 서버가 Storage 서버에서 파일을 복사해 프론트로 전송
        다운로드 흐름
        1. Next.JS에서 file_no를 인자로 API Server에 요청
        2. API Server에서는 해당 file_no 인자를 이용해서 다운로드하고자 하는 파일의 이름(file_name)과 경로(file_path)를 db에서 확인
        3. 확인한 경로를 Storage Server에 인자로 전달
        4. Storage Server에서 해당 경로에 있는 파일을 form 데이터로 다시 API Server에 전달
        5. API Server에서 form 데이터를 받으면 그것을 /data/tmp에 저장하되, 파일 이름은 db에서 확인한 파일 이름을 사용
        6. 저장한 파일을 Next.JS에 post로 전달하며, 해당 파일의 원본 이름은 헤더에 저장
    """
    temp_file_path = None  # 파일 삭제를 위해 finally에서 접근하기 위한 변수

    try:
        # 1. DB에서 파일 정보 조회
        logger.info(f"Fetching file info from DB for file_no: {payload.file_no}")
        file_info = output_DB.fetch_one_other_documents(payload.file_no)

        if not file_info:
            logger.error(f"File not found in DB for file_no: {payload.file_no}")
            raise HTTPException(status_code=404, detail="File not found in database")

        file_path = file_info['file_path']
        file_name = file_info['file_name']
        logger.info(f"File info retrieved: {file_name} at {file_path}")

        # 2. Storage 서버에서 파일 요청
        logger.info(f"Requesting file from Storage Server: {file_path}")
        try:
            response = requests.post(
                "http://192.168.50.84:10080/api/output/otherdoc_download",
                data={"file_path": file_path},
                # headers={"Authorization": STORAGE_API_KEY},
                stream=True,
                timeout=60
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to request file from storage server: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Request to storage server failed: {str(e)}")

        if response.status_code != 200:
            logger.error(f"Storage server response error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail=f"Failed to download file: {response.text}")

        # 3. 파일을 /data/tmp에 저장
        logger.info(f"Saving file to temporary directory: {TEMP_DOWNLOAD_DIR}")
        temp_file_path = os.path.join(TEMP_DOWNLOAD_DIR, file_name)

        try:
            with open(temp_file_path, "wb") as f:
                shutil.copyfileobj(response.raw, f)
            logger.info(f"File saved to {temp_file_path}")
        except Exception as e:
            logger.error(f"Failed to save file to {temp_file_path}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"File save error: {str(e)}")

        # 4. Next.js에 파일 데이터 전송
        logger.info(f"Pushing file to Next.js: {file_name}")
        push.push_to_nextjs(temp_file_path, file_name)

    except Exception as e:
        logger.error(f"Unexpected error during file transfer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    finally:
        # 5. 전송 후 임시 파일 삭제
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Temporary file deleted: {temp_file_path}")
            except Exception as e:
                logger.error(f"Failed to delete temporary file {temp_file_path}: {str(e)}", exc_info=True)


@router.post("/output/load_type")
async def api_otherdoc_type(payload: OtherDocumentPayload):
    logger.info(f"Loading document type for file_unique_id: {payload.file_unique_id}")
    try:
        result = output_DB.fetch_document_type(payload.file_unique_id)
        logger.info(f"Successfully fetched document type for file_unique_id: {payload.file_unique_id} - Result: {result}")
        return {"RESULT_CODE": 200, "RESULT_MSG": result}
    except HTTPException as e:
        logger.error(f"Error fetching document type for file_unique_id: {payload.file_unique_id} - {e.detail}", exc_info=True)
        raise e


@router.post("/output/attach_add")
async def add_attachments(
    files: List[UploadFile] = File(...),
    p_no: int = Form(...),
    doc_no: int = Form(...),
    doc_type: int = Form(...),
    univ_id: int = Form(...)
):
    """여러 첨부파일 업로드 엔드포인트"""
    logger.info(f"Starting attachments upload: p_no={p_no}, doc_no={doc_no}, doc_type={doc_type}, univ_id={univ_id}")
    attachments = []
    headers = {"Authorization": STORAGE_API_KEY}

    try:
        for file in files:
            logger.info(f"Processing attachment: {file.filename}")
            fuid = gen_file_uid()
            logger.info(f"Generated file unique ID: {fuid} for file: {file.filename}")
            
            data = {
                "fuid": fuid,
                "pid": p_no,
                "userid": univ_id,
                "doc_type": doc_type
            }
            file_content = await file.read()
            logger.info(f"Read {len(file_content)} bytes from file: {file.filename}")
            files_payload = {"file": (file.filename, file_content, file.content_type)}
            storage_url = f"{STORAGE_SERVER_URL}/attach_add"
            logger.info(f"Uploading file {file.filename} to storage server: {storage_url}")
            
            response = requests.post(storage_url, files=files_payload, data=data, headers=headers)
            if response.status_code != 200:
                logger.error(f"Storage server error for file {file.filename}: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail=f"Storage server error: {response.text}")
            
            response_data = response.json()
            file_path = response_data.get("FILE_PATH")
            if not file_path:
                logger.error(f"Invalid response from storage server for file {file.filename}: {response_data}")
                raise HTTPException(status_code=500, detail="Storage server returned invalid response")
            
            original_file_name = file.filename
            logger.info(f"File uploaded: {original_file_name} stored at {file_path}")
            db_result = output_DB.add_attachment(original_file_name, file_path, doc_type, doc_no, p_no)
            if db_result is not True:
                logger.error(f"Failed to save attachment metadata to DB for file {original_file_name}")
                raise HTTPException(status_code=500, detail="Failed to save attachment metadata to DB")
            
            attachments.append({
                "doc_a_name": original_file_name,
                "doc_a_path": file_path,
                "doc_type": doc_type,
                "doc_no": doc_no,
                "p_no": p_no
            })
            logger.info(f"Attachment processed successfully: {original_file_name}")
    
        logger.info(f"All attachments uploaded successfully: {len(attachments)} files processed")
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Attachments uploaded successfully",
            "PAYLOADS": attachments
        }
    except Exception as e:
        logger.error(f"Error in add_attachments endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading attachments: {str(e)}")


@router.post("/output/attach_load")
async def fetch_attachments(
    p_no: int = Form(...),
    doc_no: int = Form(...),
    doc_type: int = Form(...)
):
    """특정 산출물(예: 개요서, 회의록 등)에 연결된 첨부파일 목록 조회 엔드포인트."""
    logger.info(f"Fetching attachments for p_no={p_no}, doc_no={doc_no}, doc_type={doc_type}")
    try:
        attachments = output_DB.fetch_all_attachments(doc_type, doc_no, p_no)
        logger.info(f"Fetched {len(attachments)} attachments for p_no={p_no}, doc_no={doc_no}, doc_type={doc_type}")
        return {
            "RESULT_CODE": 200,
            "RESULT_MSG": "Attachments fetched successfully",
            "PAYLOADS": attachments
        }
    except Exception as e:
        logger.error(f"Error fetching attachments for p_no={p_no}, doc_no={doc_no}, doc_type={doc_type}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching attachments: {e}")


@router.post("/output/attach_download")
async def download_attachment(
    doc_a_no: int = Form(...),
    doc_type: int = Form(...),
    doc_no: int = Form(...),
    p_no: int = Form(...)
):
    logger.info(f"Downloading attachment: doc_a_no={doc_a_no}, doc_type={doc_type}, doc_no={doc_no}, p_no={p_no}")
    try:
        attachments = output_DB.fetch_all_attachments(doc_type, doc_no, p_no)
        logger.info(f"Fetched {len(attachments)} attachments from DB for p_no={p_no}, doc_no={doc_no}, doc_type={doc_type}")
        
        attachment = None
        for att in attachments:
            if int(att.get("doc_a_no", -1)) == doc_a_no:
                attachment = att
                break
        
        if not attachment:
            logger.error(f"Attachment with doc_a_no={doc_a_no} not found")
            raise HTTPException(status_code=404, detail="Attachment not found")
        
        file_path = attachment['doc_a_path']
        file_name = attachment['doc_a_name']
        logger.info(f"Found attachment: {file_name} at path {file_path}")
        
        storage_download_url = f"{STORAGE_SERVER_URL}/otherdoc_download"
        logger.info(f"Requesting file from storage server at {storage_download_url} with file_path={file_path}")
        response = requests.post(storage_download_url, data={"file_path": file_path}, stream=True)
        
        if response.status_code != 200:
            logger.error(f"Storage server error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"Storage server error: {response.text}")
        
        response.raw.decode_content = True
        temp_file_path = os.path.join(TEMP_DOWNLOAD_DIR, file_name)
        logger.info(f"Saving file to temporary path: {temp_file_path}")
        with open(temp_file_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)
        logger.info(f"File saved to {temp_file_path}")
        
        task = BackgroundTask(os.remove, temp_file_path)
        logger.info(f"Returning file response for {file_name}")
        return FileResponse(
            path=temp_file_path,
            filename=file_name,
            media_type='application/octet-stream',
            background=task
        )
    except Exception as e:
        logger.error(f"Error downloading attachment for doc_a_no={doc_a_no}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error downloading attachment: {e}")

@router.post("/output/attach_edit_name")
async def edit_attachment_name(
    doc_a_no: int = Form(...),
    new_file_name: str = Form(...)
):
    """첨부파일 이름 수정 엔드포인트"""
    logger.info(f"Starting attachment name update for doc_a_no={doc_a_no} with new_file_name='{new_file_name}'")
    try:
        result = output_DB.edit_attachment_name(doc_a_no, new_file_name)
        if result:
            logger.info(f"Attachment name updated successfully for doc_a_no={doc_a_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Attachment name updated successfully"}
        else:
            logger.error(f"Failed to update attachment name for doc_a_no={doc_a_no}")
            raise HTTPException(status_code=500, detail="Failed to update attachment name")
    except Exception as e:
        logger.error(f"Error editing attachment name for doc_a_no={doc_a_no}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error editing attachment name: {e}")


@router.post("/output/attach_edit_path")
async def edit_attachment_path(
    doc_a_no: int = Form(...),
    new_file_path: str = Form(...)
):
    """첨부파일 경로 수정 엔드포인트"""
    logger.info(f"Starting attachment path update for doc_a_no={doc_a_no} with new_file_path='{new_file_path}'")
    try:
        result = output_DB.edit_attachment_path(doc_a_no, new_file_path)
        if result:
            logger.info(f"Attachment path updated successfully for doc_a_no={doc_a_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Attachment path updated successfully"}
        else:
            logger.error(f"Failed to update attachment path for doc_a_no={doc_a_no}")
            raise HTTPException(status_code=500, detail="Failed to update attachment path")
    except Exception as e:
        logger.error(f"Error editing attachment path for doc_a_no={doc_a_no}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error editing attachment path: {e}")


@router.post("/output/attach_delete")
async def delete_attachment(
    doc_a_no: int = Form(...)
):
    """첨부파일 삭제 엔드포인트"""
    logger.info(f"Starting deletion of attachment for doc_a_no={doc_a_no}")
    try:
        result = output_DB.delete_one_attachment(doc_a_no)
        if result:
            logger.info(f"Attachment deleted successfully for doc_a_no={doc_a_no}")
            return {"RESULT_CODE": 200, "RESULT_MSG": "Attachment deleted successfully"}
        else:
            logger.error(f"Failed to delete attachment for doc_a_no={doc_a_no}")
            raise HTTPException(status_code=500, detail="Failed to delete attachment")
    except Exception as e:
        logger.error(f"Error deleting attachment for doc_a_no={doc_a_no}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting attachment: {e}")
