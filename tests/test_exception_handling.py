# tests/test_exception_handling.py

import pytest
import serial
from unittest.mock import MagicMock, patch
from Controller_Loadcell import LoadcellService, verify_loadcell_connection

class TestExceptionHandling:
    
    @pytest.mark.timeout(5)
    def test_loadcell_connect_serial_exception(self):
        """로드셀 연결 시 시리얼 예외"""
        # Given: 잘못된 포트
        # When: Serial 생성 시도
        # Then: SerialException 발생
        with pytest.raises(serial.SerialException):
            ser = serial.Serial("INVALID_PORT_XYZ", baudrate=115200, timeout=1.0)
            loadcell = LoadcellService(ser=ser)
    
    @pytest.mark.timeout(5)
    def test_loadcell_disconnect_exception(self):
        """로드셀 연결 해제 시 예외"""
        # Given: close() 시 예외 발생하는 Mock Serial
        mock_serial = MagicMock()
        mock_serial.is_open = True
        mock_serial.close.side_effect = Exception("Close error")
        
        loadcell = LoadcellService(ser=mock_serial)
        
        # When: Serial을 직접 닫을 때
        # Then: 예외 발생
        with pytest.raises(Exception, match="Close error"):
            loadcell.ser.close()
    
    @pytest.mark.timeout(5)
    def test_loadcell_connect_exception(self):
        """로드셀 연결 예외 처리"""
        # Given: Serial 생성 시 예외 발생
        with patch('serial.Serial') as mock_serial_class:
            mock_serial_class.side_effect = Exception("Port not found")
            
            # When: Serial 생성 시도
            # Then: 예외 발생
            with pytest.raises(Exception, match="Port not found"):
                ser = serial.Serial("INVALID_PORT", baudrate=115200, timeout=1.0)
                loadcell = LoadcellService(ser=ser)
    
    @pytest.mark.timeout(5)
    def test_verify_loadcell_connection_success(self):
        """로드셀 연결 검증 성공"""
        # Given: 정상 응답하는 Mock Serial
        mock_serial = MagicMock()
        mock_serial.is_open = True
        mock_serial.in_waiting = 10
        # CDL 프로토콜 응답 시뮬레이션 (4바이트 데이터)
        mock_serial.read.return_value = b'\x00\x00\x03\xe8'  # 1000 counts
        
        # When: 연결 검증
        ok, err = verify_loadcell_connection(mock_serial)
        
        # Then: 성공
        assert ok is True
        assert err == ""
    
    @pytest.mark.timeout(5)
    def test_verify_loadcell_connection_no_response(self):
        """로드셀 연결 검증 실패 - 응답 없음"""
        # Given: 응답 없는 Mock Serial
        mock_serial = MagicMock()
        mock_serial.is_open = True
        mock_serial.in_waiting = 0
        mock_serial.read.return_value = b''
        
        # When: 연결 검증
        ok, err = verify_loadcell_connection(mock_serial)
        
        # Then: 실패
        assert ok is False
        assert "응답 없음" in err or "파싱 실패" in err
