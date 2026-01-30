# tests/test_performance.py
"""
성능 및 반응 속도 테스트
"""

import pytest
import time
from unittest.mock import MagicMock  # ← 추가
from Data_Synchronizer import DataSynchronizer
from Safety_Guard import SafetyGuard
from config import safety_cfg


class TestPerformance:
    """성능 테스트"""
    
    @pytest.mark.timeout(10)
    def test_synchronizer_large_dataset_performance(self):
        """대용량 데이터 동기화 성능"""
        sync = DataSynchronizer(buffer_size=10000)
        
        # When: 10,000개 데이터 추가
        start = time.time()
        for i in range(10000):
            sync.add_position(float(i), float(i * 10))
        elapsed = time.time() - start
        
        # Then: 1초 이내에 완료
        assert elapsed < 1.0, f"Performance degraded: {elapsed:.3f}s > 1.0s"
    
    @pytest.mark.timeout(5)
    def test_guard_check_performance(self):
        """가드 체크 반응 속도"""
        mock_ui = MagicMock()
        mock_ui.DisplaceLimitMax_doubleSpinBox.value.return_value = 10.0
        guard = SafetyGuard(mock_ui, safety_cfg)
        
        # When: 1,000번 체크
        start = time.time()
        for i in range(1000):
            guard.check_displacement_limit(float(i), 0.0)
        elapsed = time.time() - start
        
        # Then: 100ms 이내
        assert elapsed < 0.1, f"Performance degraded: {elapsed:.3f}s > 0.1s"
    
    @pytest.mark.timeout(5)
    def test_data_handler_update_performance(self):
        """DataHandler 업데이트 성능"""
        from Data_Handler import DataHandler
        from UI_Updater import UIUpdater
        from Tensioning_Controller import TensioningController
        
        mock_ui = MagicMock()
        mock_ui.DisplaceLimitMax_doubleSpinBox.value.return_value = 999.0
        mock_ui.ForceLimitMax_doubleSpinBox.value.return_value = 999.0
        
        handler = DataHandler(
            ui_updater=UIUpdater(mock_ui),
            safety_guard=SafetyGuard(mock_ui, safety_cfg),
            synchronizer=DataSynchronizer(),
            tensioning=TensioningController(),
            data_receiver=MagicMock(),
            stop_callback=MagicMock()
        )
        
        # When: 1,000번 위치 업데이트
        start = time.time()
        for i in range(1000):
            handler.update_motor_position(float(i))
        elapsed = time.time() - start
        
        # Then: 200ms 이내
        assert elapsed < 0.2, f"Performance degraded: {elapsed:.3f}s > 0.2s"
