# ErrorHandler.py

import logging
from PyQt5 import QtWidgets, QtCore

logger = logging.getLogger(__name__)


class ErrorHandler:
    """중앙 집중식 에러 처리 클래스 (다국어 지원)"""
    
    # ===== 클래스 변수로 LanguageManager 저장 =====
    _language_manager = None
    
    @classmethod
    def set_language_manager(cls, lang_mgr):
        """LanguageManager 설정"""
        cls._language_manager = lang_mgr
        logger.info("ErrorHandler에 LanguageManager 연결됨")
    
    @classmethod
    def _translate(cls, key: str) -> str:
        """번역 헬퍼 메서드"""
        if cls._language_manager:
            return cls._language_manager.translate(key)
        return key  # fallback
    
    @staticmethod
    def _get_valid_parent(parent):
        """유효한 QWidget parent 반환"""
        if parent is None:
            return None
        
        # QWidget 타입이면 그대로 반환
        if isinstance(parent, QtWidgets.QWidget):
            return parent
        
        # Ui_MainWindow 같은 경우 실제 윈도우 찾기
        if hasattr(parent, 'centralwidget'):
            # centralwidget의 부모가 MainWindow
            widget = parent.centralwidget
            if widget and hasattr(widget, 'parent'):
                return widget.parent()
        
        # QMainWindow 찾기
        from PyQt5.QtWidgets import QApplication
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QtWidgets.QMainWindow):
                return widget
        
        return None
    
    # ========================================================================
    # 기본 메시지 표시 메서드
    # ========================================================================
    
    @staticmethod
    def show_error(title: str, message: str, parent=None):
        """에러 메시지 표시"""
        valid_parent = ErrorHandler._get_valid_parent(parent)
        msg_box = QtWidgets.QMessageBox(valid_parent)
        msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()
        logger.error(f"[ERROR] {title}: {message}")
    
    @staticmethod
    def show_warning(title: str, message: str, parent=None):
        """경고 메시지 표시"""
        valid_parent = ErrorHandler._get_valid_parent(parent)
        msg_box = QtWidgets.QMessageBox(valid_parent)
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()
        logger.warning(f"[WARNING] {title}: {message}")
    
    @staticmethod
    def show_info(title: str, message: str, parent=None):
        """정보 메시지 표시"""
        valid_parent = ErrorHandler._get_valid_parent(parent)
        msg_box = QtWidgets.QMessageBox(valid_parent)
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()
        logger.info(f"[INFO] {title}: {message}")
    
    @staticmethod
    def show_success(title: str, message: str, parent=None):
        """성공 메시지 표시"""
        valid_parent = ErrorHandler._get_valid_parent(parent)
        msg_box = QtWidgets.QMessageBox(valid_parent)
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec_()
        logger.info(f"[SUCCESS] {title}: {message}")
    
    @staticmethod
    def show_question(title: str, message: str, parent=None) -> bool:
        """확인 질문 표시"""
        valid_parent = ErrorHandler._get_valid_parent(parent)
        reply = QtWidgets.QMessageBox.question(
            valid_parent, 
            title, 
            message,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        result = (reply == QtWidgets.QMessageBox.Yes)
        logger.info(f"[QUESTION] {title}: {message} → {'Yes' if result else 'No'}")
        return result
    
    # ========================================================================
    # 에러 메시지 정제 (사용자 친화적으로 변환)
    # ========================================================================
    
    @classmethod
    def _sanitize_error_message(cls, raw_error: str) -> str:
        """
        기술적 오류 메시지를 사용자 친화적으로 변환 (번역 지원)
        
        Args:
            raw_error: 원본 에러 메시지
            
        Returns:
            정제된 사용자 친화적 메시지 (번역됨)
        """
        if not raw_error:
            return cls._translate("error.unknown_error")
        
        raw_lower = raw_error.lower()
        
        # 1. 권한 오류
        if "permission" in raw_lower or "액세스가 거부" in raw_error:
            return cls._translate("error.permission_denied")
        
        # 2. 포트 열기 실패
        if "could not open port" in raw_lower or "포트를 열 수 없" in raw_error:
            return cls._translate("error.port_open_failed")
        
        # 3. 타임아웃
        if "timeout" in raw_lower or "응답 없음" in raw_error or "응답이 없" in raw_error:
            return cls._translate("error.device_timeout")
        
        # 4. Modbus 오류
        if "modbus" in raw_lower and "error" in raw_lower:
            return cls._translate("error.modbus_error")
        
        # 5. CDL 프로토콜 오류 (로드셀)
        if "주소 선택 응답 없음" in raw_error or "측정 명령 응답 없음" in raw_error:
            return cls._translate("error.protocol_error")
        
        # 6. 파싱 오류
        if "파싱 실패" in raw_error or "parsing" in raw_lower:
            return cls._translate("error.parsing_error")
        
        # 7. Python 코드 오류 (프로그래밍 오류)
        if "unexpected keyword argument" in raw_lower or "attributeerror" in raw_lower or "typeerror" in raw_lower:
            return cls._translate("error.program_error")
        
        # 8. 포트가 없음
        if "no such file or directory" in raw_lower or "존재하지 않" in raw_error:
            return cls._translate("error.port_not_found")
        
        # 9. 기타 (원본 그대로 표시하되 간단히)
        first_line = raw_error.split('\n')[0]
        if len(first_line) > 100:
            return cls._translate("error.connection_generic")
        
        return first_line
    
    # ========================================================================
    # 특화된 에러 메시지 (번역 지원)
    # ========================================================================
    
    @classmethod
    def show_connection_error(cls, device: str, port: str, error_detail: str = "", parent=None):
        """
        연결 실패 전용 메시지 (사용자 친화적 + 번역 지원)
        
        Args:
            device: 장비 이름 (예: 'Motor', 'Loadcell', 'Temp Controller')
            port: 포트 이름 (예: 'COM3')
            error_detail: 원본 에러 내용 (기술적 메시지)
            parent: 부모 위젯
        """
        # 기술적 오류를 사용자 친화적으로 변환
        user_friendly_msg = cls._sanitize_error_message(error_detail)
        
        title = cls._translate("error.connection_failed")
        message = cls._translate("error.connection_failed_desc").format(
            device, port, user_friendly_msg
        )
        
        cls.show_error(title, message, parent)
        
        # 로그에는 원본 오류 메시지 기록 (디버깅용)
        logger.error(f"[{device}] 연결 실패 (포트: {port}) - 원본 오류: {error_detail}")
    
    @classmethod
    def show_communication_error(cls, device: str, error: str, parent=None):
        """
        통신 오류 전용 메시지 (사용자 친화적 + 번역 지원)
        """
        user_friendly_msg = cls._sanitize_error_message(error)
        
        title = cls._translate("error.communication_error")
        message = cls._translate("error.communication_error_desc").format(
            device, user_friendly_msg
        )
        
        cls.show_error(title, message, parent)
        
        # 로그에는 원본 오류 기록
        logger.error(f"[{device}] 통신 오류 - 원본: {error}")
    
    @classmethod
    def show_not_connected_error(cls, device_name: str, parent=None):
        """장치 미연결 에러 (번역 지원)"""
        title = cls._translate("error.not_connected")
        message = cls._translate("error.not_connected_desc").format(device_name)
        cls.show_warning(title, message, parent)
    
    @classmethod
    def show_value_error(cls, field: str, expected: str, parent=None):
        """값 오류 전용 메시지 (번역 지원)"""
        title = cls._translate("error.input_error")
        message = cls._translate("error.value_error_desc").format(field, expected)
        cls.show_warning(title, message, parent)
