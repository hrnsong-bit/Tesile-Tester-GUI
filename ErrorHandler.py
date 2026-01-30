# ErrorHandler.py
from PyQt5 import QtWidgets
import logging

logger = logging.getLogger(__name__)


class ErrorHandler:
    """통합 에러 핸들링 클래스"""
    
    @staticmethod
    def show_error(title: str, message: str, parent=None):
        """에러 메시지 표시"""
        QtWidgets.QMessageBox.critical(parent, title, message)
        logger.error(f"[ERROR] {title}: {message}")
    
    @staticmethod
    def show_warning(title: str, message: str, parent=None):
        """경고 메시지 표시"""
        QtWidgets.QMessageBox.warning(parent, title, message)
        logger.warning(f"[WARNING] {title}: {message}")
    
    @staticmethod
    def show_info(title: str, message: str, parent=None):
        """정보 메시지 표시"""
        QtWidgets.QMessageBox.information(parent, title, message)
        logger.info(f"[INFO] {title}: {message}")
    
    @staticmethod
    def show_question(title: str, message: str, parent=None) -> bool:
        """확인 질문 표시"""
        reply = QtWidgets.QMessageBox.question(
            parent, 
            title, 
            message,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        result = (reply == QtWidgets.QMessageBox.Yes)
        logger.info(f"[QUESTION] {title}: {message} → {'Yes' if result else 'No'}")
        return result
    
    # ========================================================================
    # 새로운 메서드: 에러 메시지 정제
    # ========================================================================
    
    @staticmethod
    def _sanitize_error_message(raw_error: str) -> str:
        """
        기술적 오류 메시지를 사용자 친화적으로 변환
        
        Args:
            raw_error: 원본 에러 메시지
            
        Returns:
            정제된 사용자 친화적 메시지
        """
        if not raw_error:
            return "알 수 없는 오류가 발생했습니다."
        
        raw_lower = raw_error.lower()
        
        # 1. 권한 오류
        if "permission" in raw_lower or "액세스가 거부" in raw_error:
            return "포트 접근 권한이 없습니다.\n다른 프로그램이 사용 중이거나 관리자 권한이 필요할 수 있습니다."
        
        # 2. 포트 열기 실패
        if "could not open port" in raw_lower or "포트를 열 수 없" in raw_error:
            return "포트를 열 수 없습니다.\n다른 프로그램에서 사용 중일 수 있습니다."
        
        # 3. 타임아웃
        if "timeout" in raw_lower or "응답 없음" in raw_error or "응답이 없" in raw_error:
            return "장비가 응답하지 않습니다.\n전원과 케이블 연결을 확인하세요."
        
        # 4. Modbus 오류
        if "modbus" in raw_lower and "error" in raw_lower:
            return "통신 오류가 발생했습니다.\n포트 설정을 확인하세요."
        
        # 5. CDL 프로토콜 오류 (로드셀)
        if "주소 선택 응답 없음" in raw_error or "측정 명령 응답 없음" in raw_error:
            return "올바른 장비가 아니거나 통신 설정이 잘못되었습니다.\n포트 선택을 다시 확인하세요."
        
        # 6. 파싱 오류
        if "파싱 실패" in raw_error or "parsing" in raw_lower:
            return "장비로부터 잘못된 데이터를 받았습니다.\n케이블 연결을 확인하세요."
        
        # 7. Python 코드 오류 (프로그래밍 오류)
        if "unexpected keyword argument" in raw_lower or "attributeerror" in raw_lower or "typeerror" in raw_lower:
            return "프로그램 오류가 발생했습니다.\n프로그램을 재시작하거나 관리자에게 문의하세요."
        
        # 8. 포트가 없음
        if "no such file or directory" in raw_lower or "존재하지 않" in raw_error:
            return "선택한 포트가 존재하지 않습니다.\n장비 연결을 확인하고 포트를 새로고침하세요."
        
        # 9. 기타 (원본 그대로 표시하되 간단히)
        # 너무 긴 메시지는 잘라내기 (첫 줄만 표시)
        first_line = raw_error.split('\n')[0]
        if len(first_line) > 100:
            return "연결 오류가 발생했습니다.\n장비와 포트 설정을 확인하세요."
        
        return first_line
    
    # ========================================================================
    # 특화된 에러 메시지 (개선됨)
    # ========================================================================
    
    @staticmethod
    def show_connection_error(device: str, port: str, error_detail: str = "", parent=None):
        """
        연결 실패 전용 메시지 (사용자 친화적으로 개선)
        
        Args:
            device: 장비 이름 (예: 'Motor', 'Loadcell', 'Temp Controller')
            port: 포트 이름 (예: 'COM3')
            error_detail: 원본 에러 내용 (기술적 메시지)
            parent: 부모 위젯
        """
        # 기술적 오류를 사용자 친화적으로 변환
        user_friendly_msg = ErrorHandler._sanitize_error_message(error_detail)
        
        message = (
            f"{device} 연결에 실패했습니다.\n\n"
            f"포트: {port}\n"
            f"오류: {user_friendly_msg}\n\n"
            f"다음 사항을 확인하세요:\n"
            f"• 장비가 연결되어 있는지\n"
            f"• 올바른 포트인지\n"
            f"• 다른 프로그램이 사용 중인지"
        )
        
        ErrorHandler.show_error("연결 실패", message, parent)
        
        # 로그에는 원본 오류 메시지 기록 (디버깅용)
        logger.error(f"[{device}] 연결 실패 (포트: {port}) - 원본 오류: {error_detail}")
    
    @staticmethod
    def show_communication_error(device: str, error: str, parent=None):
        """
        통신 오류 전용 메시지 (사용자 친화적으로 개선)
        """
        user_friendly_msg = ErrorHandler._sanitize_error_message(error)
        
        ErrorHandler.show_error(
            "통신 오류",
            f"{device} 통신 중 오류가 발생했습니다.\n\n"
            f"오류: {user_friendly_msg}\n\n"
            f"연결 상태를 확인하세요.",
            parent
        )
        
        # 로그에는 원본 오류 기록
        logger.error(f"[{device}] 통신 오류 - 원본: {error}")
    
    @staticmethod
    def show_value_error(field: str, expected: str, parent=None):
        """값 오류 전용 메시지"""
        ErrorHandler.show_warning(
            "입력 오류",
            f"{field} 값이 올바르지 않습니다.\n\n"
            f"예상 형식: {expected}",
            parent
        )
    
    @staticmethod
    def show_not_connected_error(device: str, parent=None):
        """미연결 상태 오류 메시지"""
        ErrorHandler.show_warning(
            "연결 필요",
            f"{device}이(가) 연결되지 않았습니다.\n\n"
            f"먼저 {device}을(를) 연결하세요.",
            parent
        )
    
    @staticmethod
    def show_success(title: str, message: str, parent=None):
        """성공 메시지 표시"""
        ErrorHandler.show_info(title, message, parent)
