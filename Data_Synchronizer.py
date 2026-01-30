# Data_Synchronizer.py
"""
데이터 동기화 담당
타임스탬프 기반으로 Motor와 Loadcell 데이터 매칭
"""

import time
import logging
from collections import deque
from interfaces import IDataSynchronizer

logger = logging.getLogger(__name__)


class DataSynchronizer(IDataSynchronizer):
    """
    타임스탬프 기반 데이터 동기화
    
    책임:
    - 위치/하중 데이터를 타임스탬프와 함께 버퍼에 저장
    - 하중 측정 시점에 가장 가까운 위치 찾기
    """
    
    def __init__(self, buffer_size: int = 100):
        self.pos_buffer = deque(maxlen=buffer_size)    # (timestamp, position_um)
        self.force_buffer = deque(maxlen=buffer_size)  # (timestamp, force_n)
        logger.info(f"DataSynchronizer 초기화 (버퍼 크기: {buffer_size})")
    
    def add_position(self, timestamp: float, pos_um: float):
        """위치 데이터 추가"""
        self.pos_buffer.append((timestamp, pos_um))
        logger.debug(f"위치 추가: {timestamp:.3f}s, {pos_um:.1f}um")
    
    def add_force(self, timestamp: float, force_n: float):
        """하중 데이터 추가"""
        self.force_buffer.append((timestamp, force_n))
        logger.debug(f"하중 추가: {timestamp:.3f}s, {force_n:.3f}N")
    
    def get_matched_position(self, force_timestamp: float) -> float:
        """
        하중 타임스탬프에 가장 가까운 위치 반환
        
        Args:
            force_timestamp: 하중 측정 시각
            
        Returns:
            매칭된 위치 (um)
        """
        if not self.pos_buffer:
            logger.warning("위치 버퍼가 비어있음")
            return 0.0
        
        # 시간 차이가 가장 작은 항목 찾기
        matched = min(
            self.pos_buffer,
            key=lambda x: abs(x[0] - force_timestamp)
        )
        
        time_diff_ms = abs(matched[0] - force_timestamp) * 1000
        
        if time_diff_ms > 50:  # 50ms 이상 차이나면 경고
            logger.warning(f"동기화 정확도 낮음: {time_diff_ms:.1f}ms")
        else:
            logger.debug(f"동기화 성공: 시간차 {time_diff_ms:.1f}ms")
        
        return matched[1]  # position_um 반환
    
    def clear(self):
        """버퍼 초기화"""
        self.pos_buffer.clear()
        self.force_buffer.clear()
        logger.info("동기화 버퍼 초기화")