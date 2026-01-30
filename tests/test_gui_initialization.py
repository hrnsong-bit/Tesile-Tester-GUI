# tests/test_gui_initialization.py
"""
GUI 초기화 관련 테스트
Main.py의 미커버 영역 테스트
"""

import pytest
from unittest.mock import MagicMock, patch


class TestGUIInitialization:
    """GUI 초기화 테스트"""
    
    @pytest.mark.timeout(10)
    def test_main_window_initialization(self, qtbot):
        """MainWindow 초기화 테스트"""
        from Main import MainWindow
        
        # When: MainWindow 생성
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Then: 핵심 컴포넌트가 초기화되어야 함
        assert window.data_handler is not None
        assert window.motor_manager is not None
        assert window.loadcell_manager is not None
        assert window.temp_manager is not None
        assert window.plot_service is not None
        assert window.speed_controller is not None
    
    @pytest.mark.timeout(5)
    def test_main_window_ui_setup(self, qtbot):
        """MainWindow UI 설정 테스트"""
        from Main import MainWindow
        
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Then: UI 요소가 존재해야 함
        assert hasattr(window.ui, 'Main_tabWidget')
        assert hasattr(window.ui, 'Com_comboBox')
        assert hasattr(window.ui, 'Jogfowerd_pushButton')
    
    @pytest.mark.timeout(5)
    def test_pretension_test_initialization(self, qtbot):
        """Pretension Test 초기화"""
        from Main import MainWindow
        
        window = MainWindow()
        qtbot.addWidget(window)
        
        # Given: 모터와 로드셀 Mock 연결
        window.motor = MagicMock()
        window.loadcell_service = MagicMock()
        
        # When: Pretension 초기화
        from Pretension_Test import PretensionTest
        pretension = PretensionTest(
            motor_service=window.motor,
            loadcell_service=window.loadcell_service,
            data_handler=window.data_handler
        )
        
        # Then: 정상 생성
        assert pretension is not None
    
    @pytest.mark.timeout(5)
    def test_com_refresh_button_click(self, qtbot):
        """COM 포트 새로고침 버튼 클릭"""
        from Main import MainWindow
        
        window = MainWindow()
        qtbot.addWidget(window)
        
        # When: Refresh 버튼 클릭
        initial_count = window.ui.Com_comboBox.count()
        window.ui.Comrefresh_pushButton.click()
        qtbot.wait(100)
        
        # Then: 크래시 없이 완료
        # (포트 개수는 시스템에 따라 다름)
        assert True
