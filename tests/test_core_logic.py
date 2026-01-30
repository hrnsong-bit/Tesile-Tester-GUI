# tests/test_core_logic.py
"""
핵심 로직 테스트
- DataHandler의 동기화 로직
- SafetyGuard의 제한 검사
- TensioningController의 상태 관리
"""

import pytest
from unittest.mock import MagicMock, patch
from Data_Handler import DataHandler
from Data_Synchronizer import DataSynchronizer
from Safety_Guard import SafetyGuard
from Tensioning_Controller import TensioningController
from UI_Updater import UIUpdater
from config import safety_cfg


class TestDataHandler:
    """DataHandler 통합 테스트"""
    
    @pytest.fixture
    def mock_ui(self):
        """Mock UI 객체"""
        ui = MagicMock()
        ui.DisplaceLimitMax_doubleSpinBox.value.return_value = 10.0  # 10mm
        ui.ForceLimitMax_doubleSpinBox.value.return_value = 1.0      # 1N
        return ui
    
    @pytest.fixture
    def handler(self, mock_ui):
        """DataHandler 인스턴스 생성 (새로운 아키텍처)"""
        # 의존성 생성
        ui_updater = UIUpdater(mock_ui)
        safety_guard = SafetyGuard(mock_ui, safety_cfg)
        synchronizer = DataSynchronizer(buffer_size=100)
        tensioning = TensioningController()
        data_receiver = MagicMock()  # PlotService Mock
        stop_callback = MagicMock()
        
        # DataHandler 생성 (의존성 주입)
        return DataHandler(
            ui_updater=ui_updater,
            safety_guard=safety_guard,
            synchronizer=synchronizer,
            tensioning=tensioning,
            data_receiver=data_receiver,
            stop_callback=stop_callback
        )
    
    def test_timestamp_matching_accuracy(self, handler):
        """타임스탬프 기반 위치-하중 매칭 정확도 검증"""
        # Given: 위치 데이터 3개 추가
        handler.sync.add_position(1.000, 100.0)
        handler.sync.add_position(1.050, 150.0)
        handler.sync.add_position(1.100, 200.0)
        
        # When: 중간 시각(1.075)에 하중 데이터 추가
        matched_pos = handler.sync.get_matched_position(1.075)
        
        # Then: 가장 가까운 위치(150.0)와 매칭되어야 함
        assert matched_pos == 150.0
    
    def test_temperature_ch1_integration(self, handler):
        """온도 CH1 데이터 통합 테스트"""
        # Given: 온도 데이터 설정
        handler.update_temperature_ch1(25.5)
        
        # Then: 내부 상태에 저장되어야 함
        assert handler.last_temp_ch1 == 25.5
    
    def test_displacement_guard(self, handler, mock_ui):
        """변위 가드 테스트"""
        # Given: 시작 위치 캡처
        handler.capture_start_position()
        handler.update_motor_position(0.0)
        
        # When: 제한값(10mm = 10000um) 초과
        handler.update_motor_position(12000.0)
        
        # Then: stop_callback이 호출되어야 함
        handler.stop_callback.assert_called_once()


class TestSafetyGuard:
    """SafetyGuard 단위 테스트"""
    
    @pytest.fixture
    def mock_ui(self):
        ui = MagicMock()
        ui.DisplaceLimitMax_doubleSpinBox.value.return_value = 5.0  # 5mm
        ui.ForceLimitMax_doubleSpinBox.value.return_value = 0.5     # 0.5N
        return ui
    
    @pytest.fixture
    def guard(self, mock_ui):
        return SafetyGuard(mock_ui, safety_cfg)
    
    def test_displacement_limit_not_exceeded(self, guard):
        """변위 제한 미초과 케이스"""
        # When: 제한값 이하로 이동
        exceeded, msg = guard.check_displacement_limit(
            current_um=4000.0, 
            start_um=0.0
        )
        
        # Then: 제한 초과하지 않음
        assert exceeded is False
        assert msg == ""
    
    def test_displacement_limit_exceeded(self, guard):
        """변위 제한 초과 케이스"""
        # When: 제한값(5mm = 5000um) 초과
        exceeded, msg = guard.check_displacement_limit(
            current_um=6000.0, 
            start_um=0.0
        )
        
        # Then: 제한 초과 감지
        assert exceeded is True
        assert "변위 가드 발동" in msg
    
    def test_force_limit_exceeded(self, guard):
        """하중 변화량 제한 초과 케이스"""
        # When: 급격한 하중 변화 (0.5N 초과)
        exceeded, msg = guard.check_force_limit(
            current_n=2.0, 
            previous_n=1.0
        )
        
        # Then: 제한 초과 감지
        assert exceeded is True
        assert "하중 가드 발동" in msg
    
    def test_guard_reset(self, guard):
        """가드 리셋 테스트"""
        # Given: 가드 발동 후
        guard.check_displacement_limit(6000.0, 0.0)
        
        # When: 리셋
        guard.reset_all()
        
        # Then: 다시 체크 가능
        exceeded, _ = guard.check_displacement_limit(6000.0, 0.0)
        assert exceeded is True  # 리셋 후 다시 발동 가능


class TestTensioningController:
    """TensioningController 단위 테스트"""
    
    @pytest.fixture
    def tensioning(self):
        return TensioningController()
    
    def test_tensioning_activation(self, tensioning):
        """텐셔닝 활성화 테스트"""
        # When: 텐셔닝 시작
        tensioning.start_tensioning(threshold_n=0.5)
        
        # Then: 활성 상태
        assert tensioning.is_active() is True
    
    def test_threshold_reached_positive(self, tensioning):
        """양수 목표 하중 도달 테스트 (인장)"""
        # Given: 목표 0.5N 설정
        tensioning.start_tensioning(threshold_n=0.5)
        
        # When: 현재 하중이 목표에 도달
        reached = tensioning.check_threshold(current_force=0.6)
        
        # Then: 도달 감지
        assert reached is True
    
    def test_threshold_reached_negative(self, tensioning):
        """음수 목표 하중 도달 테스트 (압축)"""
        # Given: 목표 -0.5N 설정
        tensioning.start_tensioning(threshold_n=-0.5)
        
        # When: 현재 하중이 목표 이하로 감소
        reached = tensioning.check_threshold(current_force=-0.6)
        
        # Then: 도달 감지
        assert reached is True
    
    def test_threshold_not_reached(self, tensioning):
        """목표 미도달 테스트"""
        # Given: 목표 0.5N 설정
        tensioning.start_tensioning(threshold_n=0.5)
        
        # When: 현재 하중이 목표 미만
        reached = tensioning.check_threshold(current_force=0.3)
        
        # Then: 미도달
        assert reached is False
    
    def test_stop_tensioning(self, tensioning):
        """텐셔닝 중지 테스트"""
        # Given: 텐셔닝 활성화
        tensioning.start_tensioning(threshold_n=0.5)
        
        # When: 중지
        tensioning.stop_tensioning()
        
        # Then: 비활성 상태
        assert tensioning.is_active() is False


class TestDataSynchronizer:
    """DataSynchronizer 단위 테스트"""
    
    @pytest.fixture
    def sync(self):
        return DataSynchronizer(buffer_size=10)
    
    def test_position_force_matching(self, sync):
        """위치-하중 매칭 정확도 테스트"""
        # Given: 위치 데이터 추가
        sync.add_position(1.000, 100.0)
        sync.add_position(1.020, 120.0)
        sync.add_position(1.040, 140.0)
        
        # When: 중간 시각에 하중 데이터 요청
        matched_pos = sync.get_matched_position(1.025)
        
        # Then: 가장 가까운 위치 반환
        assert matched_pos == 120.0
    
    def test_buffer_overflow(self, sync):
        """버퍼 오버플로우 테스트"""
        # Given: 버퍼 크기(10) 초과로 데이터 추가
        for i in range(15):
            sync.add_position(float(i), float(i * 10))
        
        # Then: 최대 10개만 유지
        assert len(sync.pos_buffer) == 10
        assert sync.pos_buffer[0][1] == 50.0  # 가장 오래된 데이터는 index 5
