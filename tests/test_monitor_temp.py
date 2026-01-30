# tests/test_monitor_temp.py (신규 생성)
import pytest
from unittest.mock import MagicMock, patch
from Monitor_temp import TempMonitor, TempWorker
from PyQt5 import QtCore


class TestTempMonitor:
    """Monitor_temp의 QTimer 기반 로직 테스트"""
    
    @pytest.mark.timeout(5)
    def test_temp_worker_timer_creation_in_thread(self, qtbot):
        """타이머가 워커 스레드에서 생성되는지"""
        mock_client = MagicMock()
        mock_client.is_socket_open.return_value = True
        
        # Given: TempWorker 생성
        worker = TempWorker(mock_client, interval_ms=100)
        
        # Then: 타이머는 아직 None
        assert worker.timer is None
        
        # When: run() 호출 (스레드 내에서 생성)
        worker.run()
        
        # Then: 타이머가 생성되어야 함
        assert worker.timer is not None
        assert worker.timer.interval() == 100
        
        # Cleanup
        worker.stop()
    
    @pytest.mark.timeout(5)
    def test_temp_monitor_data_emission(self, qtbot):
        """온도 데이터가 올바르게 방출되는지"""
        mock_client = MagicMock()
        mock_client.is_socket_open.return_value = True
        
        # Mock Modbus 응답
        mock_response = MagicMock()
        mock_response.isError.return_value = False
        mock_response.registers = [25]  # 25°C
        mock_client.read_input_registers.return_value = mock_response
        
        received_data = []
        
        def on_data(temps):
            received_data.append(temps)
        
        # Given: TempMonitor 생성
        monitor = TempMonitor(mock_client, on_data, interval_ms=100)
        
        # When: 데이터 수신 대기
        qtbot.wait(300)  # 최소 2-3번 데이터 수신
        
        # Then: 데이터가 수신되어야 함
        assert len(received_data) >= 2
        assert received_data[0][0] == 25  # CH1 = 25°C
        
        # Cleanup
        monitor.stop()
        qtbot.wait(100)
    
    @pytest.mark.timeout(5)
    def test_temp_monitor_interval_change(self, qtbot):
        """모니터링 주기 변경 테스트"""
        mock_client = MagicMock()
        mock_client.is_socket_open.return_value = True
        
        monitor = TempMonitor(mock_client, MagicMock(), interval_ms=100)
        
        # When: 주기 변경
        monitor.update_interval(200)
        qtbot.wait(100)
        
        # Then: 워커의 interval_ms가 변경되어야 함
        assert monitor.worker.interval_ms == 200
        
        # Cleanup
        monitor.stop()
    
    @pytest.mark.timeout(5)
    def test_temp_monitor_stop_before_start(self):
        """시작하지 않고 중지 호출"""
        mock_client = MagicMock()
        monitor = TempMonitor(mock_client, MagicMock(), interval_ms=100)
        
        # When: 바로 중지
        monitor.stop()
        
        # Then: 예외 없이 완료
        assert True
