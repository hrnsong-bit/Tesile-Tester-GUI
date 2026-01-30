# tests/test_integration.py
"""
전체 워크플로우 통합 테스트
"""

import pytest
import time
from unittest.mock import MagicMock, patch, Mock
from Plot_Service import PlotService


class TestIntegration:
    """전체 시스템 통합 테스트"""
    
    @pytest.fixture
    def mock_main_window(self):
        """MainWindow Mock 생성"""
        from Data_Handler import DataHandler
        from UI_Updater import UIUpdater
        from Safety_Guard import SafetyGuard
        from Data_Synchronizer import DataSynchronizer
        from Tensioning_Controller import TensioningController
        from Manager_motor import MotorManager
        from Manager_loadcell import LoadcellManager
        from config import safety_cfg
        
        # Mock UI
        mock_ui = MagicMock()
        mock_ui.DisplaceLimitMax_doubleSpinBox.value.return_value = 999.0
        mock_ui.ForceLimitMax_doubleSpinBox.value.return_value = 999.0
        
        # PlotService Mock
        plot_widget = MagicMock()
        plot_item = MagicMock()
        plot_widget.getPlotItem.return_value = plot_item
        plot_item.plot.return_value = MagicMock()
        
        plot_service = PlotService(
            main_window=MagicMock(),
            plot_widget=plot_widget
        )
        
        # DataHandler
        data_handler = DataHandler(
            ui_updater=UIUpdater(mock_ui),
            safety_guard=SafetyGuard(mock_ui, safety_cfg),
            synchronizer=DataSynchronizer(),
            tensioning=TensioningController(),
            data_receiver=plot_service,
            stop_callback=MagicMock()
        )
        
        # Managers
        motor_manager = MotorManager(data_handler=data_handler)
        loadcell_manager = LoadcellManager(data_handler=data_handler)
        
        # Mock MainWindow
        window = MagicMock()
        window.ui = mock_ui
        window.plot_service = plot_service
        window.data_handler = data_handler
        window.motor_manager = motor_manager
        window.loadcell_manager = loadcell_manager
        window.motor = None
        window.loadcell_service = None
        
        return window
    
    @pytest.mark.timeout(10)
    def test_full_test_workflow(self, mock_main_window, tmp_path):
        """전체 테스트 워크플로우"""
        window = mock_main_window
        csv_path = tmp_path / "test_workflow.csv"
        
        # Given: 장비 연결 시뮬레이션
        mock_motor_client = MagicMock()
        mock_motor_client.is_socket_open.return_value = True
        
        mock_response = MagicMock()
        mock_response.isError.return_value = False
        mock_response.registers = [0, 0]
        mock_motor_client.read_holding_registers.return_value = mock_response
        
        window.motor_manager.start_service(mock_motor_client, interval_ms=100)
        
        mock_serial = MagicMock()
        mock_serial.is_open = True
        window.loadcell_manager.start_service(mock_serial, interval_ms=100)
        
        # When: 플로팅 시작
        with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName',
                   return_value=(str(csv_path), '')):
            result = window.plot_service.start_plotting()
        
        # Then: 플로팅 시작 성공
        assert result is True, "Plotting should start successfully"
        assert window.plot_service._is_plotting is True
        
        # When: 데이터 업데이트 시뮬레이션
        window.data_handler.update_motor_position(100.0)
        window.data_handler.update_loadcell_value(0.5)
        time.sleep(0.1)
        
        # When: 테스트 중지
        window.plot_service.stop_plotting()
        
        # Then: 플로팅 중지
        assert window.plot_service._is_plotting is False
        
        # Then: CSV 파일 생성 확인
        assert csv_path.exists()
        
        # Cleanup
        window.motor_manager.stop_service()
        window.loadcell_manager.stop_service()
        time.sleep(0.2)
    
    @pytest.mark.timeout(10)
    def test_safety_guard_integration(self, mock_main_window):
        """안전 가드 통합 테스트"""
        window = mock_main_window
        
        # Given: 제한값 설정
        window.ui.DisplaceLimitMax_doubleSpinBox.value.return_value = 1.0  # 1mm
        
        # When: 시작 위치 캡처
        window.data_handler.capture_start_position()
        window.data_handler.update_motor_position(0.0)
        
        # When: 제한 초과
        window.data_handler.update_motor_position(2000.0)  # 2mm
        
        # Then: stop_callback 호출
        window.data_handler.stop_callback.assert_called()
    
    @pytest.mark.timeout(10)
    def test_data_synchronization_integration(self, mock_main_window):
        """데이터 동기화 통합 테스트"""
        window = mock_main_window
        
        # Given: 위치 데이터 추가
        window.data_handler.sync.add_position(1.000, 100.0)
        window.data_handler.sync.add_position(1.050, 150.0)
        window.data_handler.sync.add_position(1.100, 200.0)
        
        # When: 하중 데이터로 위치 조회
        matched_pos = window.data_handler.sync.get_matched_position(1.075)
        
        # Then: 가장 가까운 위치 반환
        assert matched_pos == 150.0
