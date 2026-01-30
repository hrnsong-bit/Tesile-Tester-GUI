# tests/test_csv_output.py
"""
CSV 출력 테스트
- 헤더 형식
- 데이터 행 형식
- 인코딩
"""

import pytest
import csv
from unittest.mock import MagicMock, patch
from pathlib import Path
from Plot_Service import PlotService


class TestCSVOutput:
    """CSV 로깅 기능 테스트"""
    
    @pytest.fixture
    def plot_service(self):
        """PlotService 인스턴스 생성"""
        main_window = MagicMock()
        plot_widget = MagicMock()
        
        # PlotWidget Mock 설정
        plot_item_mock = MagicMock()
        plot_widget.getPlotItem.return_value = plot_item_mock
        plot_item_mock.plot.return_value = MagicMock()
        
        return PlotService(
            main_window=main_window,
            plot_widget=plot_widget,
            ui=None,
            temp_plot_widget=None
        )
    
    def test_csv_header_format(self, plot_service, tmp_path):
        """CSV 헤더 형식 검증"""
        # Given: 임시 CSV 파일 경로
        csv_path = tmp_path / "test_output.csv"
        
        # When: 플로팅 시작 (파일 다이얼로그 Mock)
        with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName',
                   return_value=(str(csv_path), '')):
            plot_service.start_plotting()
        
        plot_service.stop_plotting()
        
        # Then: 헤더 검증
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            assert header == [
                'Time (s)', 
                'Position (um)', 
                'Load (N)',
                'Temp_CH1 (°C)'
            ]
    
    def test_csv_data_row_format(self, plot_service, tmp_path):
        """CSV 데이터 행 형식 검증"""
        # Given: 플로팅 시작
        csv_path = tmp_path / "test_data.csv"
        
        with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName',
                   return_value=(str(csv_path), '')):
            plot_service.start_plotting()
        
        # When: 데이터 3개 추가 (새로운 인터페이스 사용)
        plot_service.receive_loadcell_data(
            force_n=1.234, 
            position_um=567.89, 
            temp_ch1=25.6
        )
        plot_service.receive_loadcell_data(
            force_n=2.345, 
            position_um=678.90, 
            temp_ch1=26.1
        )
        plot_service.receive_loadcell_data(
            force_n=3.456, 
            position_um=789.01, 
            temp_ch1=26.5
        )
        
        plot_service.stop_plotting()
        
        # Then: 데이터 행 검증
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # 헤더 스킵
            
            row1 = next(reader)
            assert len(row1) == 4
            assert float(row1[2]) == pytest.approx(1.234, rel=1e-3)
            assert float(row1[1]) == pytest.approx(567.89, rel=1e-2)
            assert float(row1[3]) == pytest.approx(25.6, rel=1e-1)
    
    def test_csv_encoding_utf8(self, plot_service, tmp_path):
        """CSV UTF-8 인코딩 검증"""
        # Given: 플로팅 시작
        csv_path = tmp_path / "test_encoding.csv"
        
        with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName',
                   return_value=(str(csv_path), '')):
            plot_service.start_plotting()
        
        plot_service.stop_plotting()
        
        # Then: UTF-8로 읽을 수 있어야 함
        with open(csv_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'Time (s)' in content
            assert 'Position (um)' in content
    
    def test_csv_file_not_created_on_cancel(self, plot_service):
        """사용자가 저장을 취소하면 파일이 생성되지 않아야 함"""
        # When: 파일 다이얼로그에서 취소
        with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName',
                   return_value=('', '')):  # 빈 경로 = 취소
            result = plot_service.start_plotting()
        
        # Then: False 반환
        assert result is False
