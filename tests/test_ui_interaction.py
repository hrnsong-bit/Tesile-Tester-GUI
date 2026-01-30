# tests/test_ui_interaction.py
"""
UI 위젯 상호작용 테스트 (pytest-qt 필요)
"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets


class TestUIInteraction:
    """UI 상호작용 테스트"""
    
    @pytest.fixture
    def mock_main_window(self, qtbot):
        """Mock MainWindow 생성 (시그널 연결 포함)"""
        from GUI import Ui_MainWindow
        from Speed_Controller import SpeedController
        
        # Mock MainWindow
        window = QtWidgets.QMainWindow()
        ui = Ui_MainWindow()
        ui.setupUi(window)
        
        # SpeedController 생성
        speed_controller = SpeedController(ui)
        
        # Mock 모터 객체
        mock_motor = MagicMock()
        speed_controller.set_motor(mock_motor)
        
        # ===== 시그널 연결 (Ui_Binding.py 로직 재현) =====
        
        # 1. Jog 버튼 연결
        ui.Jogfowerd_pushButton.pressed.connect(
            lambda: mock_motor.jog_forward() if mock_motor else None
        )
        ui.Jogfowerd_pushButton.released.connect(
            lambda: mock_motor.stop_motor() if mock_motor else None
        )
        
        ui.Jogbackwerd_pushButton.pressed.connect(
            lambda: mock_motor.jog_backward() if mock_motor else None
        )
        ui.Jogbackwerd_pushButton.released.connect(
            lambda: mock_motor.stop_motor() if mock_motor else None
        )
        
        # 2. Jog 체크박스 연결
        ui.Jog_checkBox.stateChanged.connect(speed_controller.toggle_jog_mode)
        ui.Setjogspeed_pushButton.clicked.connect(speed_controller.set_jog_speed)
        
        # 3. Jog 라디오 버튼 연결
        ui.jog10_radioButton.toggled.connect(
            lambda checked: speed_controller.set_fixed_jog_speed(10, checked)
        )
        ui.jog20_radioButton.toggled.connect(
            lambda checked: speed_controller.set_fixed_jog_speed(20, checked)
        )
        ui.jog50_radioButton.toggled.connect(
            lambda checked: speed_controller.set_fixed_jog_speed(50, checked)
        )
        
        # 4. Motor 속도 라디오 버튼 연결
        ui.Motor10_radioButton.toggled.connect(
            lambda checked: speed_controller.set_fixed_run_speed(10, checked)
        )
        ui.Motor50_radioButton.toggled.connect(
            lambda checked: speed_controller.set_fixed_run_speed(50, checked)
        )
        ui.Motor100_radioButton.toggled.connect(
            lambda checked: speed_controller.set_fixed_run_speed(100, checked)
        )
        
        # 5. Motor 속도 체크박스 연결
        ui.MotorSpeed_checkBox.stateChanged.connect(
            speed_controller.toggle_motor_speed_mode
        )
        ui.Setmotorspeed_pushButton.clicked.connect(
            speed_controller.set_run_speed
        )
        
        # 속성 설정
        window.ui = ui
        window.speed_controller = speed_controller
        window.motor = mock_motor
        
        qtbot.addWidget(window)
        return window
    
    @pytest.mark.timeout(5)
    def test_speed_radio_button_selection(self, mock_main_window, qtbot):
        """속도 라디오 버튼 선택 테스트"""
        window = mock_main_window
        
        # When: 50 um/s 라디오 버튼 클릭
        window.ui.Motor50_radioButton.setChecked(True)
        qtbot.wait(100)  # UI 업데이트 대기
        
        # Then: 속도가 설정되어야 함 (50 um/s → 5.0 rps)
        expected_rps = 50.0 / 10.0  # um/s to rps
        assert window.speed_controller.run_speed == expected_rps, \
            f"Expected {expected_rps}, got {window.speed_controller.run_speed}"
    
    @pytest.mark.timeout(5)
    def test_jog_button_press_release(self, mock_main_window, qtbot):
        """Jog 버튼 눌림/뗌 테스트"""
        window = mock_main_window
        
        # When: Jog Forward 버튼 누름
        qtbot.mousePress(window.ui.Jogfowerd_pushButton, Qt.LeftButton)
        qtbot.wait(50)
        
        # Then: jog_forward 호출
        window.motor.jog_forward.assert_called_once()
        
        # When: 버튼 뗌
        qtbot.mouseRelease(window.ui.Jogfowerd_pushButton, Qt.LeftButton)
        qtbot.wait(50)
        
        # Then: stop_motor 호출
        window.motor.stop_motor.assert_called_once()
    
    @pytest.mark.timeout(5)
    def test_jog_checkbox_toggle(self, mock_main_window, qtbot):
        """Jog 체크박스 토글 테스트"""
        window = mock_main_window
        
        # ===== 수정: 초기 상태는 GUI.py의 setupUi()에 따름 =====
        # GUI.py에서 setEnabled(False)를 호출하지 않으므로 초기에 활성화됨
        initial_spinbox_state = window.ui.Jog_spinBox.isEnabled()
        initial_button_state = window.ui.Setjogspeed_pushButton.isEnabled()
        
        # When: Jog 체크박스 클릭 (사용자 정의 모드 활성화)
        window.ui.Jog_checkBox.setChecked(True)
        qtbot.wait(100)
        
        # Then: SpinBox와 버튼이 활성화되어야 함
        assert window.ui.Jog_spinBox.isEnabled() is True
        assert window.ui.Setjogspeed_pushButton.isEnabled() is True
        
        # When: 다시 체크 해제 (프리셋 모드)
        window.ui.Jog_checkBox.setChecked(False)
        qtbot.wait(100)
        
        # Then: 비활성화되어야 함
        assert window.ui.Jog_spinBox.isEnabled() is False, \
            "Jog_spinBox should be disabled when checkbox is unchecked"
        assert window.ui.Setjogspeed_pushButton.isEnabled() is False, \
            "Setjogspeed_pushButton should be disabled when checkbox is unchecked"
    
    @pytest.mark.timeout(5)
    def test_jog_backward_button(self, mock_main_window, qtbot):
        """Jog Backward 버튼 테스트"""
        window = mock_main_window
        
        # When: Jog Backward 버튼 누름
        qtbot.mousePress(window.ui.Jogbackwerd_pushButton, Qt.LeftButton)
        qtbot.wait(50)
        
        # Then: jog_backward 호출
        window.motor.jog_backward.assert_called_once()
        
        # When: 버튼 뗌
        qtbot.mouseRelease(window.ui.Jogbackwerd_pushButton, Qt.LeftButton)
        qtbot.wait(50)
        
        # Then: stop_motor 호출 (2번째 호출)
        assert window.motor.stop_motor.call_count == 1
    
    @pytest.mark.timeout(5)
    def test_motor_speed_checkbox_toggle(self, mock_main_window, qtbot):
        """Motor 속도 체크박스 토글 테스트"""
        window = mock_main_window
        
        # ===== 수정: 초기 상태 확인하지 않고 동작 검증 =====
        # 초기 상태가 어떻든 체크박스 토글 후 상태 변화 확인
        
        # When: 체크박스 클릭 (사용자 정의 모드)
        window.ui.MotorSpeed_checkBox.setChecked(True)
        qtbot.wait(100)
        
        # Then: 활성화
        assert window.ui.MotorSpeed_spinBox.isEnabled() is True, \
            "MotorSpeed_spinBox should be enabled when checkbox is checked"
        assert window.ui.Setmotorspeed_pushButton.isEnabled() is True, \
            "Setmotorspeed_pushButton should be enabled when checkbox is checked"
        
        # When: 체크 해제 (프리셋 모드)
        window.ui.MotorSpeed_checkBox.setChecked(False)
        qtbot.wait(100)
        
        # Then: 비활성화
        assert window.ui.MotorSpeed_spinBox.isEnabled() is False, \
            "MotorSpeed_spinBox should be disabled when checkbox is unchecked"
        assert window.ui.Setmotorspeed_pushButton.isEnabled() is False, \
            "Setmotorspeed_pushButton should be disabled when checkbox is unchecked"
    
    @pytest.mark.timeout(5)
    def test_jog_speed_radio_button_selection(self, mock_main_window, qtbot):
        """Jog 속도 라디오 버튼 선택 테스트"""
        window = mock_main_window
        
        # When: 50 um/s Jog 라디오 버튼 선택
        window.ui.jog50_radioButton.setChecked(True)
        qtbot.wait(100)
        
        # Then: set_jog_speed가 호출되어야 함
        window.motor.set_jog_speed.assert_called()
        
        # 호출된 인자 확인 (50 um/s → 5.0 rps)
        call_args = window.motor.set_jog_speed.call_args
        assert call_args is not None
        rps_value = call_args[0][0]
        expected_rps = 50.0 / 10.0
        assert abs(rps_value - expected_rps) < 0.01, \
            f"Expected {expected_rps}, got {rps_value}"
    
    @pytest.mark.timeout(5)
    def test_multiple_radio_button_switches(self, mock_main_window, qtbot):
        """여러 라디오 버튼 전환 테스트"""
        window = mock_main_window
        
        # When: 10 → 50 → 100 순서로 선택
        window.ui.Motor10_radioButton.setChecked(True)
        qtbot.wait(50)
        assert window.speed_controller.run_speed == 1.0, \
            f"Expected 1.0, got {window.speed_controller.run_speed}"
        
        window.ui.Motor50_radioButton.setChecked(True)
        qtbot.wait(50)
        assert window.speed_controller.run_speed == 5.0, \
            f"Expected 5.0, got {window.speed_controller.run_speed}"
        
        window.ui.Motor100_radioButton.setChecked(True)
        qtbot.wait(50)
        assert window.speed_controller.run_speed == 10.0, \
            f"Expected 10.0, got {window.speed_controller.run_speed}"
    
    @pytest.mark.timeout(5)
    def test_checkbox_enables_spinbox_interaction(self, mock_main_window, qtbot):
        """체크박스로 SpinBox 상호작용 제어 테스트"""
        window = mock_main_window
        
        # Given: 체크박스 활성화
        window.ui.MotorSpeed_checkBox.setChecked(True)
        qtbot.wait(100)
        
        # When: SpinBox 값 변경
        window.ui.MotorSpeed_spinBox.setValue(123)
        qtbot.wait(50)
        
        # Then: 값이 설정되어야 함
        assert window.ui.MotorSpeed_spinBox.value() == 123
        
        # When: 버튼 클릭
        window.ui.Setmotorspeed_pushButton.click()
        qtbot.wait(50)
        
        # Then: SpeedController에 반영되어야 함
        expected_rps = 123.0 / 10.0  # 12.3 rps
        assert abs(window.speed_controller.run_speed - expected_rps) < 0.01, \
            f"Expected {expected_rps}, got {window.speed_controller.run_speed}"
