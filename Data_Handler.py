# Data_Handler.py
"""
데이터 흐름 조정자 (Coordinator)

역할:
- 각 컴포넌트 간 데이터 전달
- 이벤트 처리 순서 관리
"""

import time
import logging
from typing import Callable

from interfaces import (
    IDataReceiver, 
    IUIUpdater, 
    ISafetyGuard, 
    IDataSynchronizer,
    ITensioningController
)

logger = logging.getLogger(__name__)


class DataHandler:
    """
    데이터 흐름 조정자
    
    단일 책임: 데이터를 적절한 컴포넌트로 라우팅
    """
    
    def __init__(
        self,
        ui_updater: IUIUpdater,
        safety_guard: ISafetyGuard,
        synchronizer: IDataSynchronizer,
        tensioning: ITensioningController,
        data_receiver: IDataReceiver,  # PlotService 등
        stop_callback: Callable
    ):
        """
        의존성 주입 (Dependency Injection)
        
        Args:
            ui_updater: UI 업데이트 담당
            safety_guard: 안전 가드 담당
            synchronizer: 데이터 동기화 담당
            tensioning: 텐셔닝 제어 담당
            data_receiver: 데이터 수신 담당 (PlotService)
            stop_callback: 긴급 정지 콜백
        """
        self.ui_updater = ui_updater
        self.guard = safety_guard
        self.sync = synchronizer
        self.tension = tensioning
        self.receiver = data_receiver
        self.stop_callback = stop_callback
        
        # 상태 변수
        self.start_pos_um = 0.0
        self.last_pos_um = 0.0
        self.last_force = 0.0
        self.last_temp_ch1 = 0.0
        
        logger.info("DataHandler 초기화 완료 (의존성 주입)")
    
    # ========================================================================
    # 모터 데이터 처리
    # ========================================================================
    
    def update_motor_position(self, pos_um: float):
        """
        모터 위치 업데이트
        
        처리 순서:
        1. UI 업데이트
        2. 데이터 동기화 버퍼에 추가
        3. 안전 가드 검사 (텐셔닝 중이 아닐 때만)
        """
        try:
            timestamp = time.time()
            self.last_pos_um = float(pos_um)
            
            # 1. UI 업데이트
            self.ui_updater.update_motor_position(pos_um)
            
            # 2. 동기화 버퍼에 추가
            self.sync.add_position(timestamp, pos_um)
            
            # 3. 안전 가드 (텐셔닝 중엔 체크 안 함)
            if not self.tension.is_active():
                exceeded, message = self.guard.check_displacement_limit(
                    pos_um, 
                    self.start_pos_um
                )
                
                if exceeded:
                    self.stop_callback(reason=message)
        
        except Exception as e:
            logger.error(f"모터 위치 처리 실패: {e}", exc_info=True)
    
    # ========================================================================
    # 로드셀 데이터 처리
    # ========================================================================
    
    def update_loadcell_value(self, force_n: float):
        """
        로드셀 값 업데이트
        
        처리 순서:
        1. UI 업데이트
        2. 동기화 버퍼에 추가
        3. 매칭된 위치 찾기
        4. 데이터 수신자(PlotService)에 전달
        5. 텐셔닝 체크
        6. 안전 가드 체크 (텐셔닝 중이 아닐 때만)
        """
        try:
            timestamp = time.time()
            previous_force = self.last_force
            self.last_force = float(force_n)
            
            # 1. UI 업데이트
            self.ui_updater.update_loadcell_value(force_n)
            
            # 2. 동기화 버퍼에 추가
            self.sync.add_force(timestamp, force_n)
            
            # 3. 매칭된 위치 찾기
            matched_pos = self.sync.get_matched_position(timestamp)
            
            # 4. 데이터 수신자에 전달 (CSV 로깅, 그래프 등)
            self.receiver.receive_loadcell_data(
                force_n, 
                matched_pos,
                self.last_temp_ch1
            )
            
            # 5. 텐셔닝 체크
            if self.tension.is_active():
                if self.tension.check_threshold(force_n):
                    self.tension.stop_tensioning()
                    self.stop_callback(reason="텐셔닝 목표 도달")
                return  # 텐셔닝 중엔 안전 가드 체크 안 함
            
            # 6. 안전 가드
            exceeded, message = self.guard.check_force_limit(
                force_n, 
                previous_force
            )
            
            if exceeded:
                self.stop_callback(reason=message)
        
        except Exception as e:
            logger.error(f"로드셀 값 처리 실패: {e}", exc_info=True)
    
    # ========================================================================
    # 온도 데이터 처리
    # ========================================================================
    
    def update_temperature_ch1(self, temp_ch1: float):
        """
        온도 CH1 업데이트 (Test 로그용)
        
        Args:
            temp_ch1: CH1 온도 (°C)
        """
        try:
            if temp_ch1 is not None:
                self.last_temp_ch1 = float(temp_ch1)
                logger.debug(f"CH1 온도 업데이트: {temp_ch1:.1f}°C")
        
        except Exception as e:
            logger.error(f"온도 업데이트 실패: {e}")
    
    # ========================================================================
    # 상태 관리
    # ========================================================================
    
    def capture_start_position(self):
        """테스트 시작 위치 캡처"""
        self.start_pos_um = self.last_pos_um
        logger.info(f"시작 위치 캡처: {self.start_pos_um:.1f} um")
    
    def reset_guards(self):
        """모든 가드 리셋"""
        self.guard.reset_all()
        logger.info("모든 가드 리셋")
    
    def start_tensioning(self, threshold_n: float):
        """텐셔닝 시작"""
        self.tension.start_tensioning(threshold_n)
        self.reset_guards()
    
    def stop_tensioning(self):
        """텐셔닝 중지"""
        self.tension.stop_tensioning()