from fastapi import APIRouter, HTTPException, File, UploadFile
import os

router = APIRouter()

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/file/upload")
async def api_file_upload(file: UploadFile = File(...)):
    """파일 업로드"""
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        return {"RESULT_CODE": 200, "RESULT_MSG": "File uploaded successfully", "FILE_NAME": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during file upload: {str(e)}")
