# Safety_Guard.py
"""
안전 가드 로직 담당
변위/하중 제한 검사
"""

import logging
from typing import Tuple
from interfaces import ISafetyGuard

logger = logging.getLogger(__name__)


class SafetyGuard(ISafetyGuard):
    """
    안전 제한 검사
    
    책임:
    - 변위 제한 초과 감지
    - 하중 변화량 제한 초과 감지
    - 가드 상태 관리
    """
    
    def __init__(self, ui, config):
        """
        Args:
            ui: GUI 객체 (설정값 읽기용)
            config: 설정 객체
        """
        self.ui = ui
        self.config = config
        
        self._disp_guard_fired = False
        self._force_guard_fired = False
        
        logger.info("SafetyGuard 초기화 완료")
    
    def check_displacement_limit(
        self, 
        current_um: float, 
        start_um: float
    ) -> Tuple[bool, str]:
        """
        변위 제한 검사
        
        Args:
            current_um: 현재 위치
            start_um: 시작 위치
            
        Returns:
            (제한 초과 여부, 메시지)
        """
        if self._disp_guard_fired:
            return (False, "")
        
        # UI에서 제한값 읽기
        try:
            limit_mm = float(self.ui.DisplaceLimitMax_doubleSpinBox.value())
        except Exception:
            limit_mm = 0.0
        
        if limit_mm <= 0:
            return (False, "")
        
        limit_um = limit_mm * 1000.0
        tolerance_um = self.config.DISPLACEMENT_TOLERANCE_UM
        
        displacement = abs(current_um - start_um)
        
        if displacement >= (limit_um - tolerance_um):
            self._disp_guard_fired = True
            message = (
                f"변위 가드 발동\n"
                f"현재: {displacement:.1f} um\n"
                f"제한: {limit_um:.1f} um"
            )
            logger.warning(f"[GUARD:DISP] {message}")
            return (True, message)
        
        return (False, "")
    
    def check_force_limit(
        self, 
        current_n: float, 
        previous_n: float
    ) -> Tuple[bool, str]:
        """
        하중 변화량 제한 검사
        
        Args:
            current_n: 현재 하중
            previous_n: 이전 하중
            
        Returns:
            (제한 초과 여부, 메시지)
        """
        if self._force_guard_fired:
            return (False, "")
        
        # UI에서 제한값 읽기
        try:
            limit_n = float(self.ui.ForceLimitMax_doubleSpinBox.value())
        except Exception:
            limit_n = 0.0
        
        if limit_n <= 0:
            return (False, "")
        
        force_delta = abs(current_n - previous_n)
        
        if force_delta >= limit_n:
            self._force_guard_fired = True
            message = (
                f"하중 가드 발동\n"
                f"변화량: {force_delta:.3f} N\n"
                f"제한: {limit_n:.3f} N"
            )
            logger.warning(f"[GUARD:FORCE] {message}")
            return (True, message)
        
        return (False, "")
    
    def reset_displacement_guard(self):
        """변위 가드 리셋"""
        self._disp_guard_fired = False
        logger.info("변위 가드 리셋")
    
    def reset_force_guard(self):
        """하중 가드 리셋"""
        self._force_guard_fired = False
        logger.info("하중 가드 리셋")
    
    def reset_all(self):
        """모든 가드 리셋"""
        self.reset_displacement_guard()
        self.reset_force_guard()
        logger.info("모든 가드 리셋")