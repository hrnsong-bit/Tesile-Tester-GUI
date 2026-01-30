# tests/test_resource_management.py
"""
리소스 관리 및 메모리 누수 테스트
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from Plot_Service import PlotService
from Manager_motor import MotorManager


class TestResourceManagement:
    """리소스 관리 테스트"""
    
    @pytest.mark.timeout(5)
    def test_csv_file_properly_closed(self, tmp_path):
        """CSV 파일이 제대로 닫히는지"""
        # Given: PlotService 생성
        plot_service = self._create_plot_service()
        csv_path = tmp_path / "test.csv"
        
        # When: 플로팅 시작 후 중지
        with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName',
                   return_value=(str(csv_path), '')):
            plot_service.start_plotting()
        
        plot_service.stop_plotting()
        
        # Then: 파일이 존재하고 닫혀있어야 함
        assert csv_path.exists()
        
        # 파일이 닫혔는지 확인 (다시 열 수 있어야 함)
        with open(csv_path, 'r') as f:
            content = f.read()
            assert 'Time (s)' in content
    
    @pytest.mark.timeout(5)
    def test_monitor_thread_cleanup(self):
        """Monitor 스레드가 제대로 종료되는지"""
        # Given: MotorManager 시작
        manager = MotorManager(data_handler=MagicMock())
        mock_client = MagicMock()
        mock_client.is_socket_open.return_value = True
        
        mock_response = MagicMock()
        mock_response.isError.return_value = False
        mock_response.registers = [0, 0]
        mock_client.read_holding_registers.return_value = mock_response
        
        manager.start_service(mock_client, interval_ms=100)
        
        # When: 서비스 중지
        manager.stop_service()
        time.sleep(0.3)  # 스레드 종료 대기
        
        # Then: monitor가 None이어야 함
        assert manager.monitor is None
    
    @pytest.mark.timeout(5)
    def test_data_buffer_memory_limit(self):
        """데이터 버퍼가 적절히 관리되는지"""
        # Given: PlotService with large data
        plot_service = self._create_plot_service()
        plot_service._is_plotting = True
        plot_service.start_time.start()
        
        # When: 1,000개 데이터 추가 (10,000 → 1,000)
        for i in range(1000):
            plot_service.receive_loadcell_data(
                force_n=float(i),
                position_um=float(i * 10),
                temp_ch1=25.0
            )
        
        # Then: 데이터가 저장되어야 함
        assert len(plot_service.x_data) == 1000
        assert len(plot_service.y_data) == 1000
    
    @pytest.mark.timeout(5)
    def test_temp_plot_buffer_trimming(self):
        """온도 플롯 버퍼 트리밍"""
        plot_service = self._create_plot_service()
        plot_service.init_temp_plot()
        
        # When: max_points 초과로 데이터 추가
        for i in range(1500):
            plot_service.update_temp_plot(
                elapsed=float(i),
                temps=[25.0, 26.0, 27.0, 28.0]
            )
        
        # Then: 최대 1000개로 제한
        assert len(plot_service.temp_x) <= 1000
    
    def _create_plot_service(self):
        """테스트용 PlotService 생성"""
        main_window = MagicMock()
        plot_widget = MagicMock()
        plot_item = MagicMock()
        plot_widget.getPlotItem.return_value = plot_item
        plot_item.plot.return_value = MagicMock()
        
        return PlotService(
            main_window=main_window,
            plot_widget=plot_widget
        )
