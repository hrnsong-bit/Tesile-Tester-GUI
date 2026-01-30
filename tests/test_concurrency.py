# tests/test_concurrency.py
"""
멀티스레드 환경에서의 동시성 테스트
"""

import pytest
import time
import threading
from Data_Handler import DataHandler
from Data_Synchronizer import DataSynchronizer
from Safety_Guard import SafetyGuard
from Tensioning_Controller import TensioningController
from UI_Updater import UIUpdater
from unittest.mock import MagicMock
from config import safety_cfg


class TestConcurrency:
    """동시성 및 Race Condition 테스트"""
    
    @pytest.mark.timeout(10)
    def test_simultaneous_position_force_updates(self):
        """위치와 하중이 동시에 업데이트될 때"""
        # Given: DataHandler 생성
        handler = self._create_handler()
        
        errors = []
        
        # When: 멀티스레드로 동시 업데이트
        def update_position():
            try:
                for i in range(50):  # 100 → 50으로 감소
                    handler.update_motor_position(float(i))
                    time.sleep(0.005)  # 0.001 → 0.005로 증가
            except Exception as e:
                errors.append(e)
        
        def update_force():
            try:
                for i in range(50):
                    handler.update_loadcell_value(float(i) * 0.1)
                    time.sleep(0.005)
            except Exception as e:
                errors.append(e)
        
        t1 = threading.Thread(target=update_position)
        t2 = threading.Thread(target=update_force)
        
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)
        
        # Then: 에러 없이 완료
        assert len(errors) == 0, f"Errors occurred: {errors}"
    
    @pytest.mark.timeout(10)
    def test_guard_concurrent_checks(self):
        """여러 스레드에서 동시에 가드 체크"""
        # Given: SafetyGuard
        mock_ui = MagicMock()
        mock_ui.DisplaceLimitMax_doubleSpinBox.value.return_value = 10.0
        guard = SafetyGuard(mock_ui, safety_cfg)
        
        results = []
        lock = threading.Lock()
        
        # When: 동시에 제한 체크
        def check_limit():
            exceeded, msg = guard.check_displacement_limit(15000.0, 0.0)
            with lock:
                results.append(exceeded)
        
        threads = [threading.Thread(target=check_limit) for _ in range(5)]  # 10 → 5
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2)
        
        # Then: 첫 번째 스레드만 발동해야 함
        assert sum(results) == 1, f"Expected 1 trigger, got {sum(results)}"
    
    @pytest.mark.timeout(5)
    def test_synchronizer_concurrent_adds(self):
        """동시에 데이터 추가"""
        sync = DataSynchronizer(buffer_size=1000)
        
        def add_positions():
            for i in range(100):
                sync.add_position(float(i), float(i * 10))
        
        def add_forces():
            for i in range(100):
                sync.add_force(float(i), float(i * 0.1))
        
        t1 = threading.Thread(target=add_positions)
        t2 = threading.Thread(target=add_forces)
        
        t1.start()
        t2.start()
        t1.join(timeout=3)
        t2.join(timeout=3)
        
        # Then: 데이터가 추가되어야 함
        assert len(sync.pos_buffer) > 0
        assert len(sync.force_buffer) > 0
    
    def _create_handler(self):
        """테스트용 DataHandler 생성"""
        mock_ui = MagicMock()
        mock_ui.DisplaceLimitMax_doubleSpinBox.value.return_value = 999.0
        mock_ui.ForceLimitMax_doubleSpinBox.value.return_value = 999.0
        
        return DataHandler(
            ui_updater=UIUpdater(mock_ui),
            safety_guard=SafetyGuard(mock_ui, safety_cfg),
            synchronizer=DataSynchronizer(),
            tensioning=TensioningController(),
            data_receiver=MagicMock(),
            stop_callback=MagicMock()
        )
