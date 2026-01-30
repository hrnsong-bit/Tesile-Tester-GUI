# tests/test_temp_manager.py
"""
Manager_temp.py의 제어 로직 테스트
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from Manager_temp import TempManager


class TestTempManager:
    """TempManager의 제어 로직 테스트"""
    
    @pytest.fixture
    def mock_ui(self):
        """실제 UI 구조를 반영한 Mock UI"""
        ui = MagicMock()
        
        # Control Settings 위젯
        ui.temp_sv_input = MagicMock()
        ui.temp_sv_input.value.return_value = 50.0
        
        ui.at_exec_combo = MagicMock()
        ui.at_exec_combo.currentIndex.return_value = 1  # ON (실행)
        
        # 안정화 설정 위젯
        ui.temp_stability_enabled = MagicMock()
        ui.temp_stability_enabled.isChecked.return_value = True
        
        ui.temp_stability_range = MagicMock()
        ui.temp_stability_range.value.return_value = 2.0
        
        ui.temp_stability_time = MagicMock()
        ui.temp_stability_time.value.return_value = 5
        
        # 채널 표시 위젯
        ui.temp_channels = {
            1: {'lbl': MagicMock(), 'chk': MagicMock()},
            2: {'lbl': MagicMock(), 'chk': MagicMock()},
            3: {'lbl': MagicMock(), 'chk': MagicMock()},
            4: {'lbl': MagicMock(), 'chk': MagicMock()},
        }
        
        return ui
    
    @pytest.mark.timeout(5)
    @patch('PyQt5.QtWidgets.QMessageBox.warning')  # ===== 추가: 경고창 Mock =====
    @patch('PyQt5.QtWidgets.QMessageBox.information')  # ===== 추가: 정보창 Mock =====
    @patch('PyQt5.QtWidgets.QMessageBox.critical')  # ===== 추가: 에러창 Mock =====
    def test_start_control_success(
        self, 
        mock_critical,
        mock_information, 
        mock_warning,
        mock_ui
    ):
        """온도 제어 시작 성공 (QMessageBox Mock 처리)"""
        # Given: TempManager 생성
        manager = TempManager(mock_ui)
        
        mock_client = MagicMock()
        mock_client.is_socket_open.return_value = True
        
        # Modbus 응답 설정
        mock_write_response = MagicMock()
        mock_write_response.isError.return_value = False
        mock_client.write_register.return_value = mock_write_response
        
        mock_read_response = MagicMock()
        mock_read_response.isError.return_value = False
        mock_read_response.registers = [25]
        mock_client.read_input_registers.return_value = mock_read_response
        
        # When: 서비스 시작
        manager.start_service(mock_client, interval_ms=100)
        time.sleep(0.2)
        
        # When: 제어 시작
        success = manager.start_control()
        
        # Then: 성공
        assert success is True, "start_control()이 True를 반환해야 함"
        assert manager.control_active is True, "control_active가 True여야 함"
        assert manager.control_start_time is not None, "control_start_time이 설정되어야 함"
        
        # ===== 추가: QMessageBox.information이 호출되었는지 확인 =====
        assert mock_information.called, "성공 시 정보 메시지가 표시되어야 함"
        
        # Cleanup
        manager.stop_service()
        time.sleep(0.2)
    
    @pytest.mark.timeout(5)
    @patch('PyQt5.QtWidgets.QMessageBox.warning')  # ===== 추가 =====
    def test_start_control_no_controller(self, mock_warning, mock_ui):
        """제어기 없이 시작 시도 (경고창 Mock)"""
        # Given: TempManager (controller=None)
        manager = TempManager(mock_ui)
        
        # When: controller가 None인 상태에서 시작
        success = manager.start_control()
        
        # Then: 실패
        assert success is False, "controller가 None이면 False 반환"
        
        # ===== 추가: 경고 메시지가 표시되었는지 확인 =====
        assert mock_warning.called, "controller 없으면 경고 메시지 표시"
    
    @pytest.mark.timeout(5)
    @patch('PyQt5.QtWidgets.QMessageBox.critical')  # ===== 추가 =====
    def test_start_control_modbus_error(self, mock_critical, mock_ui):
        """Modbus 명령 실패 시 (에러창 Mock)"""
        # Given: TempManager 생성
        manager = TempManager(mock_ui)
        
        mock_client = MagicMock()
        mock_client.is_socket_open.return_value = True
        
        # Modbus 명령 실패 설정
        mock_error_response = MagicMock()
        mock_error_response.isError.return_value = True
        mock_client.write_register.return_value = mock_error_response
        
        mock_read_response = MagicMock()
        mock_read_response.isError.return_value = False
        mock_read_response.registers = [20]
        mock_client.read_input_registers.return_value = mock_read_response
        
        manager.start_service(mock_client, interval_ms=100)
        time.sleep(0.2)
        
        # When: 제어 시작 (Modbus 쓰기 실패)
        success = manager.start_control()
        
        # Then: 실패
        assert success is False, "모든 Modbus 명령이 실패하면 False 반환"
        
        # ===== 추가: 에러 메시지가 표시되었는지 확인 =====
        assert mock_critical.called, "Modbus 에러 시 critical 메시지 표시"
        
        # Cleanup
        manager.stop_service()
        time.sleep(0.2)
    
    @pytest.mark.timeout(5)
    @patch('PyQt5.QtWidgets.QMessageBox.information')  # ===== 추가 =====
    def test_stop_control_resets_state(self, mock_information, mock_ui):
        """제어 정지 시 상태 초기화 (정보창 Mock)"""
        # Given: 제어 시작된 상태
        manager = TempManager(mock_ui)
        
        mock_client = MagicMock()
        mock_client.is_socket_open.return_value = True
        
        mock_response = MagicMock()
        mock_response.isError.return_value = False
        mock_client.write_register.return_value = mock_response
        
        mock_read_response = MagicMock()
        mock_read_response.isError.return_value = False
        mock_read_response.registers = [30]
        mock_client.read_input_registers.return_value = mock_read_response
        
        manager.start_service(mock_client, interval_ms=100)
        time.sleep(0.2)
        
        # 제어 플래그 강제 활성화 (start_control 스킵)
        manager.control_active = True
        manager.control_start_time = time.time()
        
        # When: 제어 정지
        success = manager.stop_control()
        
        # Then: 상태 초기화
        assert success is True, "stop_control()이 True를 반환해야 함"
        assert manager.control_active is False, "control_active가 False여야 함"
        assert manager.control_start_time is None, "control_start_time이 None이어야 함"
        
        # ===== 추가: 정보 메시지 확인 =====
        assert mock_information.called, "정지 시 정보 메시지 표시"
        
        # Cleanup
        manager.stop_service()
        time.sleep(0.2)
    
    @pytest.mark.timeout(5)
    def test_stop_control_no_controller(self, mock_ui):
        """제어기 없이 정지 시도"""
        # Given: TempManager (controller=None)
        manager = TempManager(mock_ui)
        
        # When: controller가 None인 상태에서 정지
        success = manager.stop_control()
        
        # Then: 실패
        assert success is False, "controller가 None이면 False 반환"
    
    @pytest.mark.timeout(5)
    def test_update_all_with_control_active(self, mock_ui):
        """제어 활성화 시 update_all 동작"""
        # Given: 제어 시작된 상태
        manager = TempManager(mock_ui)
        manager.control_active = True
        manager.control_start_time = time.time()
        
        # When: 온도 데이터 업데이트
        temps = [25.0, 26.5, 27.0, 28.5]
        manager.update_all(temps)
        
        # Then: UI 라벨이 업데이트되어야 함
        for i in range(1, 5):
            manager.ui.temp_channels[i]['lbl'].setText.assert_called()
    
    @pytest.mark.timeout(5)
    def test_update_all_with_control_inactive(self, mock_ui):
        """제어 비활성화 시 update_all 동작"""
        # Given: 제어가 비활성화된 상태
        manager = TempManager(mock_ui)
        manager.control_active = False
        manager.start_time = time.time()  # ===== 추가: start_time 설정 =====
        
        # When: 온도 데이터 업데이트
        temps = [20.0, 21.0, 22.0, 23.0]
        manager.update_all(temps)
        
        # Then: UI 라벨은 업데이트
        for i in range(1, 5):
            manager.ui.temp_channels[i]['lbl'].setText.assert_called()
