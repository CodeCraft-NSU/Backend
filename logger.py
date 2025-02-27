"""                                                          
   CodeCraft PMS Backend Project                             
                                                                              
   파일명   : logger.py                                                          
   생성자   : 김창환                                
                                                                              
   생성일   : 2025/02/15
   업데이트 : 2025/02/15
                                                                             
   설명     : 디버깅 관련 로깅 함수 정의
"""

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger("project_logger")

uvicorn_access_logger = logging.getLogger("uvicorn.access") # 액세스 로그도 남게 추가 (25.02.28)
uvicorn_access_logger.propagate = True