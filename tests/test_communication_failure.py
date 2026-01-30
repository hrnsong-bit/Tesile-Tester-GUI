# tests/test_communication_failure.py
"""
통신 장애 시 복구 및 에러 핸들링 테스트
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from Manager_motor import MotorManager
from Manager_loadcell import LoadcellManager
from Controller_motor import MotorService


class TestCommunicationFailure:
    """통신 장애 상황 테스트"""
    
    @pytest.mark.timeout(5)  # 5초 타임아웃 설정
    def test_motor_connection_lost_during_test(self):
        """테스트 중 모터 연결 끊김"""
        # Given: 모터가 연결된 상태
        motor_manager = MotorManager(data_handler=MagicMock())
        mock_client = MagicMock()
        mock_client.is_socket_open.return_value = True
        mock_client.connect.return_value = True
        
        # Mock read response
        mock_response = MagicMock()
        mock_response.isError.return_value = False
        mock_response.registers = [0, 0]
        mock_client.read_holding_registers.return_value = mock_response
        
        motor_manager.start_service(mock_client, interval_ms=100)
        
        # When: 갑자기 연결 끊김
        mock_client.is_socket_open.return_value = False
        
        # Then: Controller는 여전히 존재 (예외 없음)
        assert motor_manager.controller is not None
        
        # Cleanup: 서비스 중지
        motor_manager.stop_service()
        time.sleep(0.2)  # 스레드 종료 대기
    
    @pytest.mark.timeout(5)
    def test_loadcell_serial_not_open(self):
        """로드셀 시리얼 포트가 닫혀있을 때"""
        # Given: 로드셀 연결
        loadcell_manager = LoadcellManager(data_handler=MagicMock())
        mock_serial = MagicMock()
        mock_serial.is_open = False  # 포트가 닫혀있음
        
        # When: 서비스 시작 시도
        loadcell_manager.start_service(mock_serial, interval_ms=100)
        
        # Then: Controller는 생성되지만 에러 없이 처리
        assert loadcell_manager.controller is not None
        
        # Cleanup
        loadcell_manager.stop_service()
        time.sleep(0.2)
    
    @pytest.mark.timeout(5)
    def test_modbus_crc_error_handling(self):
        """Modbus CRC 에러 처리"""
        # Given: Modbus 클라이언트
        mock_client = MagicMock()
        
        # When: CRC 에러 응답
        mock_response = MagicMock()
        mock_response.isError.return_value = True
        mock_client.read_holding_registers.return_value = mock_response
        
        # Then: 안전하게 처리되어야 함
        motor = MotorService(mock_client)
        position = motor.read_target_position()
        
        # 에러 시 기본값(0) 반환
        assert position == 0
    
    @pytest.mark.timeout(5)
    def test_motor_manager_stop_without_start(self):
        """시작하지 않고 중지 호출"""
        # Given: MotorManager 생성만
        motor_manager = MotorManager(data_handler=MagicMock())
        
        # When: 서비스를 시작하지 않고 중지
        motor_manager.stop_service()
        
        # Then: 예외 없이 완료
        assert motor_manager.controller is None
    
    @pytest.mark.timeout(5)
    def test_loadcell_manager_double_stop(self):
        """중복 중지 호출"""
        # Given: LoadcellManager 시작 후 중지
        loadcell_manager = LoadcellManager(data_handler=MagicMock())
        mock_serial = MagicMock()
        mock_serial.is_open = True
        
        loadcell_manager.start_service(mock_serial, interval_ms=100)
        loadcell_manager.stop_service()
        time.sleep(0.2)
        
        # When: 다시 중지 호출
        loadcell_manager.stop_service()
        
        # Then: 예외 없이 완료
        assert loadcell_manager.controller is None
