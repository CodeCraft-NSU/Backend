from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from docx import Document
from datetime import datetime, date  # date를 명확히 가져옴
import pymysql, os, sys

sys.path.append(os.path.abspath('/data/Database Project'))  # Database Project와 연동하기 위해 사용
import output_DB

router = APIRouter()

class ConverterPayload(BaseModel):
    doc_type: int
    doc_s_no: int

@router.post("/docs/convert")
async def docs_convert(payload: ConverterPayload):
    if payload.doc_type == 1:  # 회의록
        meeting_data = output_DB.fetch_one_meeting_minutes(payload.doc_s_no)
        if not meeting_data:
            raise HTTPException(status_code=404, detail="Meeting data not found")
        print("Fetched meeting data:", meeting_data)

        try:
            doc = Document("/data/Docs_Template/MM.docx")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Template loading error: {e}")

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    cell.text = cell.text.replace("{f1}", meeting_data.get("doc_m_title", ""))
                    # 날짜를 문자열로 변환
                    cell.text = cell.text.replace(
                        "{f2}",
                        meeting_data.get("doc_m_date", "").strftime("%Y-%m-%d")
                        if isinstance(meeting_data.get("doc_m_date"), date)  # 수정: datetime.date -> date
                        else str(meeting_data.get("doc_m_date", ""))
                    )
                    cell.text = cell.text.replace("{f3}", meeting_data.get("doc_m_manager", ""))
                    cell.text = cell.text.replace("{f4}", meeting_data.get("doc_m_loc", ""))
                    cell.text = cell.text.replace("{f5}", meeting_data.get("doc_m_member", ""))
                    cell.text = cell.text.replace("{f6}", meeting_data.get("doc_m_content", ""))
                    cell.text = cell.text.replace("{f7}", meeting_data.get("doc_m_result", ""))
                    # 참석자 이름과 학번 조회하는 기능 구현 필요
                    for i in range(1, 21):  # 사용하지 않은 기호 삭제
                        cell.text = cell.text.replace(f"{{f{i}}}", "")
                        
        output_path = f"/data/Backend Project/temp/회의록_{payload.doc_s_no}.docx"
        try:
            doc.save(output_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Document saving error: {e}")
        return JSONResponse(content={"message": "Document created successfully", "file_path": output_path}) # 파일 return 기능 구현 필요
    raise HTTPException(status_code=400, detail="Invalid document type")
