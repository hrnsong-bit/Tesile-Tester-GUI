# tests/conftest.py
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_ui():
    """재사용 가능한 Mock UI"""
    ui = MagicMock()
    
    # Setting 탭 라벨
    ui.En0Positionnow_label = MagicMock()
    ui.Load0Currentnow_label = MagicMock()
    
    # Test 탭 라벨
    ui.test_pos_label = MagicMock()
    ui.test_load_label = MagicMock()
    
    # 안전 한계 SpinBox
    ui.DisplaceLimitMax_doubleSpinBox = MagicMock()
    ui.DisplaceLimitMax_doubleSpinBox.value.return_value = 10.0
    
    ui.ForceLimitMax_doubleSpinBox = MagicMock()
    ui.ForceLimitMax_doubleSpinBox.value.return_value = 5.0
    
    return ui

@pytest.fixture
def mock_modbus_client():
    """재사용 가능한 Mock Modbus 클라이언트"""
    client = MagicMock()
    client.is_socket_open.return_value = True
    
    # 기본 응답 설정
    read_result = MagicMock()
    read_result.isError.return_value = False
    read_result.registers = [0, 0]
    client.read_holding_registers.return_value = read_result
    
    write_result = MagicMock()
    write_result.isError.return_value = False
    client.write_register.return_value = write_result
    client.write_registers.return_value = write_result
    
    return client

@pytest.fixture
def mock_serial():
    """재사용 가능한 Mock Serial"""
    ser = MagicMock()
    ser.is_open = True
    ser.in_waiting = 0
    return ser
