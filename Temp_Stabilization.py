# Temp_Stabilization.py
"""
온도 안정화 감지
설정한 범위 내에서 설정한 시간 동안 유지되면 알림
"""

import time
import logging
from PyQt5 import QtCore

logger = logging.getLogger(__name__)


class TempStabilizationDetector(QtCore.QObject):
    """
    온도 안정화 감지기
    
    조건:
    - 목표 온도 ± 범위 내에 진입
    - 설정한 시간 동안 범위 내 유지
    - 범위를 벗어나면 타이머 리셋
    """
    
    # 안정화 완료 시그널
    stabilization_achieved = QtCore.pyqtSignal(float, float, float)  # (target, range, duration_min)
    
    def __init__(self):
        super().__init__()
        
        # 설정값
        self.target_temp = 0.0
        self.tolerance_range = 2.0  # ±2°C
        self.required_duration_sec = 300  # 5분 (초 단위)
        self.enabled = True
        
        # 상태
        self.in_range_start_time = None
        self.stabilized = False
        self.last_check_time = 0
        
        logger.info("TempStabilizationDetector 초기화")
    
    def set_target(self, target_temp: float, tolerance_range: float, duration_minutes: int):
        """
        안정화 조건 설정
        
        Args:
            target_temp: 목표 온도 (°C)
            tolerance_range: 허용 범위 (±°C)
            duration_minutes: 유지 시간 (분)
        """
        self.target_temp = target_temp
        self.tolerance_range = tolerance_range
        self.required_duration_sec = duration_minutes * 60
        
        # 상태 초기화
        self.in_range_start_time = None
        self.stabilized = False
        
        logger.info(
            f"[Stabilization] 목표 설정: {target_temp}°C ±{tolerance_range}°C, "
            f"{duration_minutes}분 유지"
        )
    
    def set_enabled(self, enabled: bool):
        """안정화 감지 활성화/비활성화"""
        self.enabled = enabled
        if not enabled:
            self.reset()
        logger.info(f"[Stabilization] 감지 {'활성화' if enabled else '비활성화'}")
    
    def reset(self):
        """상태 초기화"""
        self.in_range_start_time = None
        self.stabilized = False
        logger.debug("[Stabilization] 상태 리셋")
    
    def check_temperature(self, current_temp: float):
        """
        현재 온도 체크
        
        Args:
            current_temp: 현재 온도 (°C)
        """
        if not self.enabled:
            return
        
        if self.stabilized:
            return  # 이미 안정화 완료
        
        # 현재 시간
        now = time.time()
        
        # 1초에 한 번만 체크 (너무 자주 체크하지 않음)
        if now - self.last_check_time < 1.0:
            return
        self.last_check_time = now
        
        # 범위 내에 있는지 확인
        lower_bound = self.target_temp - self.tolerance_range
        upper_bound = self.target_temp + self.tolerance_range
        
        is_in_range = (lower_bound <= current_temp <= upper_bound)
        
        if is_in_range:
            # 범위 내 진입
            if self.in_range_start_time is None:
                self.in_range_start_time = now
                logger.info(
                    f"[Stabilization] 범위 진입: {current_temp:.1f}°C "
                    f"(목표: {self.target_temp}°C ±{self.tolerance_range}°C)"
                )
            
            # 유지 시간 체크
            elapsed_sec = now - self.in_range_start_time
            remaining_sec = self.required_duration_sec - elapsed_sec
            
            # 10초마다 진행 상황 로그
            if int(elapsed_sec) % 10 == 0 and remaining_sec > 0:
                remaining_min = remaining_sec / 60
                logger.debug(
                    f"[Stabilization] 유지 중... {elapsed_sec:.0f}초 경과 "
                    f"(남은 시간: {remaining_min:.1f}분)"
                )
            
            # 목표 시간 도달
            if elapsed_sec >= self.required_duration_sec:
                self.stabilized = True
                logger.info(
                    f"[Stabilization] ✓ 안정화 완료! "
                    f"{self.target_temp}°C ±{self.tolerance_range}°C 범위에서 "
                    f"{self.required_duration_sec/60:.1f}분 유지됨"
                )
                
                # 시그널 발생
                self.stabilization_achieved.emit(
                    self.target_temp,
                    self.tolerance_range,
                    self.required_duration_sec / 60
                )
        
        else:
            # 범위 벗어남
            if self.in_range_start_time is not None:
                elapsed_sec = now - self.in_range_start_time
                logger.warning(
                    f"[Stabilization] 범위 이탈: {current_temp:.1f}°C "
                    f"({elapsed_sec:.0f}초 유지 후 이탈) - 타이머 리셋"
                )
                self.in_range_start_time = None
    
    def get_status(self) -> dict:
        """
        현재 상태 반환
        
        Returns:
            dict: {
                'in_range': bool,
                'elapsed_sec': float,
                'remaining_sec': float,
                'stabilized': bool
            }
        """
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
