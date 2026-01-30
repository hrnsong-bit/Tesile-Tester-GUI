# tests/test_edge_cases.py
"""
경계 조건 및 특수 케이스 테스트
"""

import pytest
from Data_Synchronizer import DataSynchronizer
from Safety_Guard import SafetyGuard
from unittest.mock import MagicMock
from config import safety_cfg


class TestEdgeCases:
    """엣지 케이스 테스트"""
    
    def test_zero_displacement_guard(self):
        """변위 제한이 0일 때"""
        mock_ui = MagicMock()
        mock_ui.DisplaceLimitMax_doubleSpinBox.value.return_value = 0.0
        guard = SafetyGuard(mock_ui, safety_cfg)
        
        # When: 제한이 0이면 체크하지 않아야 함
        exceeded, msg = guard.check_displacement_limit(1000.0, 0.0)
        
        # Then: 제한 없음
        assert exceeded is False
    
    def test_negative_force_values(self):
        """음수 하중값 처리"""
        mock_ui = MagicMock()
        mock_ui.ForceLimitMax_doubleSpinBox.value.return_value = 1.0
        guard = SafetyGuard(mock_ui, safety_cfg)
        
        # When: 압축 하중 (-값)에서 급변
        exceeded, msg = guard.check_force_limit(
            current_n=-2.0,
            previous_n=-0.5
        )
        
        # Then: 절대값 변화량으로 체크
        assert exceeded is True
    
    def test_empty_synchronizer_buffer(self):
        """동기화 버퍼가 비어있을 때"""
        sync = DataSynchronizer()
        
        # When: 위치 데이터가 없을 때 매칭 요청
        matched = sync.get_matched_position(1.0)
        
        # Then: 0.0 반환 (안전한 기본값)
        assert matched == 0.0
    
    def test_very_large_position_values(self):
        """매우 큰 위치값 처리 (오버플로우 방지)"""
        from Controller_motor import MotorService
        
        mock_client = MagicMock()
        motor = MotorService(mock_client)
        
        # When: 32bit 최대값 근처의 위치
        u32_max = 0xFFFFFFFF
        s32_result = motor._s32(u32_max)
        
        # Then: 올바르게 음수로 변환
        assert s32_result == -1
    
    def test_simultaneous_guard_triggers(self):
        """변위와 하중 가드가 동시에 발동"""
        from Data_Handler import DataHandler
        from UI_Updater import UIUpdater
        from Tensioning_Controller import TensioningController
        
        mock_ui = MagicMock()
        mock_ui.DisplaceLimitMax_doubleSpinBox.value.return_value = 1.0  # 1mm
        mock_ui.ForceLimitMax_doubleSpinBox.value.return_value = 0.1     # 0.1N
        
        mock_stop = MagicMock()
        
        handler = DataHandler(
            ui_updater=UIUpdater(mock_ui),
            safety_guard=SafetyGuard(mock_ui, safety_cfg),
            synchronizer=DataSynchronizer(),
            tensioning=TensioningController(),
            data_receiver=MagicMock(),
            stop_callback=mock_stop
        )
        
        handler.capture_start_position()
        
        # When: 변위와 하중 모두 초과
        handler.update_motor_position(0.0)
        handler.update_motor_position(2000.0)  # 2mm 초과
        handler.update_loadcell_value(0.0)
        handler.update_loadcell_value(5.0)     # 급변
        
        # Then: stop_callback이 최소 1번 호출
        assert mock_stop.call_count >= 1
