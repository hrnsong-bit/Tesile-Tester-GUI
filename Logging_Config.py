# Logging_Config.py
import logging
import logging.handlers
import sys

def setup_logging():

    # 1. 포맷터 정의 (로그 형식 설정)
    # [시간] - [로거 이름(파일)] - [레벨] - [메시지]
    formatter = logging.Formatter(
        '%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 2. 루트 로거 가져오기 (모든 로거의 최상위)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) # 모든 레벨(DEBUG 이상)을 처리하도록 설정
    
    # 핸들러 중복 추가 방지
    if logger.hasHandlers():
        logger.handlers.clear()

    # 3. 핸들러 1: 콘솔(터미널) 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # 콘솔에는 DEBUG 이상 모두 출력
    console_handler.setFormatter(formatter)
    
    # 4. 핸들러 2: 파일 핸들러 (exe 배포용)
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            'app.log',          # 로그 파일 이름
            maxBytes=5*1024*1024, # 5 MB
            backupCount=2,        # 최대 2개 파일 유지 (app.log, app.log.1)
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO) # 파일에는 INFO 이상만 기록 (DEBUG 제외)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    except PermissionError:
        print(f"[Logging_Config] 경고: app.log 파일에 대한 쓰기 권한이 없습니다. 파일 로깅을 건너뜁니다.")
    except Exception as e:
        print(f"[Logging_Config] 파일 핸들러 설정 중 오류 발생: {e}")
    
    # 5. 로거에 핸들러 추가
    logger.addHandler(console_handler)

    logging.info("================== 로깅 시스템 시작 ==================")