# interfaces.py
"""
추상 인터페이스 정의
의존성 역전 원칙(DIP)을 위한 계약(Contract) 정의
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple


class IDataReceiver(ABC):
    """데이터 수신 인터페이스 (PlotService, Logger 등이 구현)"""
    
    @abstractmethod
    def receive_motor_data(self, elapsed: float, displacement_um: float):
        """모터 데이터 수신"""
        pass
    
    @abstractmethod
    def receive_loadcell_data(self, force_n: float, position_um: float, temp_ch1: float):
        """로드셀 데이터 수신 (동기화된 위치 포함)"""
        pass
    
    @abstractmethod
    def receive_temp_data(self, elapsed: float, temps: list):
        """온도 데이터 수신"""
        pass


class IUIUpdater(ABC):
    """UI 업데이트 인터페이스"""
    
    @abstractmethod
    def update_motor_position(self, pos_um: float):
        """모터 위치 라벨 업데이트"""
        pass
    
    @abstractmethod
    def update_loadcell_value(self, force_n: float):
        """로드셀 값 라벨 업데이트"""
        pass
    
    @abstractmethod
    def update_temperature(self, channel: int, temp: float):
        """온도 라벨 업데이트"""
        pass


class ISafetyGuard(ABC):
    """안전 가드 인터페이스"""
    
    @abstractmethod
    def check_displacement_limit(self, current_um: float, start_um: float) -> Tuple[bool, str]:
        """
        변위 제한 검사
        Returns: (제한 초과 여부, 메시지)
        """
        pass
    
    @abstractmethod
    def check_force_limit(self, current_n: float, previous_n: float) -> Tuple[bool, str]:
        """하중 제한 검사"""
        pass
    
    @abstractmethod
    def reset_displacement_guard(self):
        """변위 가드 리셋"""
        pass
    
    @abstractmethod
    def reset_force_guard(self):
        """하중 가드 리셋"""
        pass


class IDataSynchronizer(ABC):
    """데이터 동기화 인터페이스"""
    
    @abstractmethod
    def add_position(self, timestamp: float, pos_um: float):
        """위치 데이터 버퍼에 추가"""
        pass
    
    @abstractmethod
    def add_force(self, timestamp: float, force_n: float):
        """하중 데이터 버퍼에 추가"""
        pass
    
    @abstractmethod
    def get_matched_position(self, force_timestamp: float) -> float:
        """
        하중 타임스탬프에 매칭되는 위치 반환
        Returns: 매칭된 position (um)
        """
        pass


class ITensioningController(ABC):
    """텐셔닝 제어 인터페이스"""
    
    @abstractmethod
    def start_tensioning(self, threshold_n: float):
        """텐셔닝 시작"""
        pass
    
    @abstractmethod
    def stop_tensioning(self):
        """텐셔닝 중지"""
        pass
    
    @abstractmethod
    def check_threshold(self, current_force: float) -> bool:
        """
        목표 하중 도달 여부 확인
        Returns: True if 도달
        """
        pass
    
    @abstractmethod
    def is_active(self) -> bool:
        """텐셔닝 활성 상태 여부"""
        pass