# 산출물 관련 기능
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import mysql_connection  # MySQL 연결 기능 수행

router = APIRouter()

class summary_document_add(BaseModel): # 개요서 간단본 추가 클래스
    pname: str # 프로젝트 제목
    pteam: str # 팀 구성
    psummary: str # 프로젝트 개요
    pstart: str # 일정 시작일
    pend: str # 일정 종료일
    prange: str # 프로젝트 범위
    poutcomes: str # 기대 성과

class overview_document_add(BaseModel): # 개요서 상세본 추가 클래스
    poverview: str # 프로젝트 개요
    pteam: str # 팀 구성 및 역할 분담
    pgoals: str # 세부 목표
    pstart: str # 일정 시작일
    pend: str # 일정 종료일
    prange: str # 프로젝트 범위
    pstack: str # 기술 스택 및 도구

class meeting_minutes_add(BaseModel):  # 회의록 추가 클래스
    main_agenda: str  # 주요 안건
    date_time: str  # 일시
    location: str  # 장소
    participants: str  # 참여자
    responsible_person: str  # 책임자
    meeting_content: str  # 회의 내용
    meeting_outcome: str  # 회의 결과

class ReqSpecAdd(BaseModel):  # 요구사항 명세서 추가 클래스
    # 기능 요구사항
    feature_name: str # 이름
    description: str # 설명
    priority: int # 우선 순위
    # 비기능 요구사항
    non_functional_requirement_name: str # 이름
    non_functional_description: str # 설명
    non_functional_priority: int # 우선순위
    # 시스템 요구사항
    system_item: str # 항목
    system_description: str # 설명

@router.post("/output/sum_doc_add")
async def api_summary_document_add(payload: summary_document_add):
    # DB에 접속
    db_connect()  
    # 가상의 함수 add_summary_document()를 사용한다고 가정
    document_id = add_summary_document(
        pname=payload.pname,
        pteam=payload.pteam,
        psummary=payload.psummary,
        pstart=payload.pstart,
        pend=payload.pend,
        prange=payload.prange,
        poutcomes=payload.poutcomes
    )
    
    if document_id is None:
        raise HTTPException(status_code=400, detail="Summary document addition failed")
    
    return JSONResponse(content={"message": "Summary document added successfully", "document_id": document_id})

@router.post("/output/ovr_doc_add")
async def api_overview_document_add(payload: overview_document_add):
    # DB에 접속
    db_connect()  
    # 가상의 함수 add_overview_document()를 사용한다고 가정
    document_id = add_overview_document(
        poverview=payload.poverview,
        pteam=payload.pteam,
        pgoals=payload.pgoals,
        pstart=payload.pstart,
        pend=payload.pend,
        prange=payload.prange,
        pstack=payload.pstack
    )
    
    if document_id is None:
        raise HTTPException(status_code=400, detail="Overview document addition failed")
    
    return JSONResponse(content={"message": "Overview document added successfully", "document_id": document_id})

@router.post("/output/mm_add")
async def api_meeting_minutes_add(payload: meeting_minutes_add):
    # DB에 접속
    db_connect()  
    # 가상의 함수 add_meeting_minutes()를 사용한다고 가정
    meeting_id = add_meeting_minutes(
        main_agenda=payload.main_agenda,
        date_time=payload.date_time,
        location=payload.location,
        participants=payload.participants,
        responsible_person=payload.responsible_person,
        meeting_content=payload.meeting_content,
        meeting_outcome=payload.meeting_outcome
    )
    
    if meeting_id is None:
        raise HTTPException(status_code=400, detail="Meeting minutes addition failed")
    
    return JSONResponse(content={"message": "Meeting minutes added successfully", "meeting_id": meeting_id})

@router.post("/output/reqspec_add")
async def api_reqspec_add(payload: ReqSpecAdd):
    # DB에 접속
    db_connect()  
    # 가상의 함수 add_reqspec()를 사용한다고 가정
    reqspec_id = add_reqspec(
        feature_name=payload.feature_name,
        description=payload.description,
        priority=payload.priority,
        non_functional_requirement_name=payload.non_functional_requirement_name,
        non_functional_description=payload.non_functional_description,
        non_functional_priority=payload.non_functional_priority,
        system_item=payload.system_item,
        system_description=payload.system_description
    )
    
    if reqspec_id is None:
        raise HTTPException(status_code=400, detail="Requirements specification addition failed")
    
    return JSONResponse(content={"message": "Requirements specification added successfully", "reqspec_id": reqspec_id})
