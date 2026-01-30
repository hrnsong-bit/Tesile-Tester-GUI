# tests/test_error_handler.py (신규 생성)
import pytest
from unittest.mock import MagicMock, patch
from ErrorHandler import ErrorHandler


class TestErrorHandler:
    """ErrorHandler 통합 테스트"""
    
    @pytest.mark.timeout(5)
    def test_show_error_calls_qmessagebox(self, qtbot):
        """show_error가 QMessageBox를 호출하는지"""
        with patch('ErrorHandler.QtWidgets.QMessageBox.critical') as mock_critical:
            # When: 에러 메시지 표시
            ErrorHandler.show_error("Test Error", "Test Message")
            
            # Then: QMessageBox.critical 호출
            mock_critical.assert_called_once()
    
    @pytest.mark.timeout(5)
    def test_show_connection_error_format(self):
        """연결 실패 메시지 포맷 검증"""
        with patch('ErrorHandler.QtWidgets.QMessageBox.critical') as mock_critical:
            # When: 연결 에러 표시
            ErrorHandler.show_connection_error("Motor", "COM3", "Port not found")
            
            # Then: 호출됨
            mock_critical.assert_called_once()
            
            # 메시지 포맷 검증
            args = mock_critical.call_args[0]
            message = args[2]
            assert "Motor" in message
            assert "COM3" in message
            assert "Port not found" in message
