# Tensioning_Controller.py
"""
텐셔닝 제어 로직
"""

import logging
from interfaces import ITensioningController

logger = logging.getLogger(__name__)


class TensioningController(ITensioningController):
    """
    텐셔닝 제어
    
    책임:
    - 텐셔닝 상태 관리
    - 목표 하중 도달 감지
    """
    
    def __init__(self):
        self._is_active = False
        self._threshold_n = 0.0
        logger.info("TensioningController 초기화")
    
    def start_tensioning(self, threshold_n: float):
        """
        텐셔닝 시작
        
        Args:
            threshold_n: 목표 하중 (양수: 인장, 음수: 압축)
        """
        if threshold_n == 0.0:
            logger.error("텐셔닝 목표 하중은 0이 될 수 없음")
            return
        
        self._is_active = True
        self._threshold_n = threshold_n
        
        mode = "인장(+)" if threshold_n > 0 else "압축(-)"
        logger.info(f"텐셔닝 시작: {mode}, 목표={abs(threshold_n):.3f}N")
    
    def stop_tensioning(self):
        """텐셔닝 중지"""
        self._is_active = False
        logger.info("텐셔닝 중지")
    
    def check_threshold(self, current_force: float) -> bool:
        """
        목표 하중 도달 여부 확인
        
        Args:
            current_force: 현재 하중
            
        Returns:
            True if 목표 도달
        """
        if not self._is_active:
            return False
        
        # 양수 목표 (인장): current >= target
        if self._threshold_n > 0:
            reached = (current_force >= self._threshold_n)
        
        # 음수 목표 (압축): current <= target
        else:
            reached = (current_force <= self._threshold_n)
        
        if reached:
            logger.info(
                f"텐셔닝 목표 도달: "
                f"현재={current_force:.3f}N, 목표={self._threshold_n:.3f}N"
            )
        
        return reached
    
    def is_active(self) -> bool:
        """텐셔닝 활성 상태"""
        return self._is_active