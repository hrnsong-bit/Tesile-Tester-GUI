"""
온도 안정화 감지
"""

import time
import logging
from PyQt5 import QtCore
from config import stabilization_cfg  # ===== 추가 =====

logger = logging.getLogger(__name__)


class TempStabilizationDetector(QtCore.QObject):
    """온도 안정화 감지기"""
    
    stabilization_achieved = QtCore.pyqtSignal(float, float, float)
    
    def __init__(self):
        super().__init__()
        
        # 설정값
        self.target_temp = 0.0
        self.tolerance_range = 2.0
        self.required_duration_sec = 300
        self.enabled = True
        
        # 상태
        self.in_range_start_time = None
        self.stabilized = False
        self.last_check_time = 0
        
        logger.info("TempStabilizationDetector 초기화")
    
    def set_target(self, target_temp: float, tolerance_range: float, duration_minutes: int):
        """안정화 조건 설정"""
        self.target_temp = target_temp
        self.tolerance_range = tolerance_range
        self.required_duration_sec = duration_minutes * 60
        
        self.in_range_start_time = None
        self.stabilized = False
        
        logger.info(
            f"[Stabilization] 목표: {target_temp}°C ±{tolerance_range}°C, {duration_minutes}분"
        )
    
    def set_enabled(self, enabled: bool):
        """활성화/비활성화"""
        self.enabled = enabled
        if not enabled:
            self.reset()
        logger.info(f"[Stabilization] {'활성화' if enabled else '비활성화'}")
    
    def reset(self):
        """상태 초기화"""
        self.in_range_start_time = None
        self.stabilized = False
        logger.debug("[Stabilization] 리셋")
    
    def check_temperature(self, current_temp: float):
        """현재 온도 체크"""
        if not self.enabled or self.stabilized:
            return
        
        now = time.time()
        
        # ===== 수정: 매직 넘버 → config =====
        # 1초에 한 번만 체크
        if now - self.last_check_time < stabilization_cfg.CHECK_INTERVAL_SEC:  # ← 1.0 대신
            return
        self.last_check_time = now
        
        # 범위 확인
        lower_bound = self.target_temp - self.tolerance_range
        upper_bound = self.target_temp + self.tolerance_range
        is_in_range = (lower_bound <= current_temp <= upper_bound)
        
        if is_in_range:
            if self.in_range_start_time is None:
                self.in_range_start_time = now
                logger.info(f"[Stabilization] 범위 진입: {current_temp:.1f}°C")
            
            elapsed_sec = now - self.in_range_start_time
            remaining_sec = self.required_duration_sec - elapsed_sec
            
            # ===== 수정: 매직 넘버 → config =====
            # 10초마다 로그
            if int(elapsed_sec) % stabilization_cfg.LOG_INTERVAL_SEC == 0 and remaining_sec > 0:  # ← 10 대신
                logger.debug(
                    f"[Stabilization] {elapsed_sec:.0f}초 경과 "
                    f"(남은 시간: {remaining_sec/60:.1f}분)"
                )
            
            # 목표 도달
            if elapsed_sec >= self.required_duration_sec:
                self.stabilized = True
                logger.info(f"[Stabilization] ✓ 안정화 완료!")
                
                self.stabilization_achieved.emit(
                    self.target_temp,
                    self.tolerance_range,
                    self.required_duration_sec / 60
                )
        
        else:
            # 범위 이탈
            if self.in_range_start_time is not None:
                elapsed_sec = now - self.in_range_start_time
                logger.warning(
                    f"[Stabilization] 범위 이탈: {current_temp:.1f}°C "
                    f"({elapsed_sec:.0f}초 후 이탈)"
                )
                self.in_range_start_time = None
    
    def get_status(self) -> dict:
        """현재 상태 반환"""
        if not self.enabled:
            return {
                'in_range': False,
                'elapsed_sec': 0,
                'remaining_sec': self.required_duration_sec,
                'stabilized': False
            }
        
        if self.in_range_start_time is None:
            return {
                'in_range': False,
                'elapsed_sec': 0,
                'remaining_sec': self.required_duration_sec,
                'stabilized': self.stabilized
            }
        
        elapsed = time.time() - self.in_range_start_time
        remaining = max(0, self.required_duration_sec - elapsed)
        
        return {
            'in_range': True,
            'elapsed_sec': elapsed,
            'remaining_sec': remaining,
            'stabilized': self.stabilized
        }
