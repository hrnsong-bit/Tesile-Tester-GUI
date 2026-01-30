"""
Settings_Manager.py
사용자 설정 영속화 담당

QSettings를 사용하여 프로그램 종료 후에도 설정값 유지
"""

from PyQt5.QtCore import QSettings
import logging

logger = logging.getLogger(__name__)


class SettingsManager:
    """
    사용자 설정 관리자
    
    저장 위치:
    - Windows: HKEY_CURRENT_USER\\Software\\YourCompany\\UTM_System
    - Linux: ~/.config/YourCompany/UTM_System.conf
    - macOS: ~/Library/Preferences/com.YourCompany.UTM_System.plist
    """
    
    def __init__(self, organization="YourCompany", application="UTM_System"):
        self.settings = QSettings(organization, application)
        logger.info(f"설정 파일 위치: {self.settings.fileName()}")
    
    # ========================================================================
    # Motor 설정
    # ========================================================================
    
    def save_motor_port(self, port: str):
        """마지막 사용한 모터 포트 저장"""
        self.settings.setValue("motor/port", port)
        logger.debug(f"모터 포트 저장: {port}")
    
    def load_motor_port(self) -> str:
        """마지막 사용한 모터 포트 불러오기"""
        port = self.settings.value("motor/port", "", type=str)
        logger.debug(f"모터 포트 불러오기: {port}")
        return port
    
    def save_motor_baudrate(self, baudrate: int):
        """마지막 사용한 모터 보드레이트 저장"""
        self.settings.setValue("motor/baudrate", baudrate)
    
    def load_motor_baudrate(self) -> int:
        """마지막 사용한 모터 보드레이트 불러오기"""
        return self.settings.value("motor/baudrate", 9600, type=int)
    
    def save_last_speed(self, speed_um: float):
        """마지막 사용한 속도 저장"""
        self.settings.setValue("motor/last_speed", speed_um)
    
    def load_last_speed(self) -> float:
        """마지막 사용한 속도 불러오기"""
        return self.settings.value("motor/last_speed", 50.0, type=float)
    
    # ========================================================================
    # Loadcell 설정
    # ========================================================================
    
    def save_loadcell_port(self, port: str):
        """마지막 사용한 로드셀 포트 저장"""
        self.settings.setValue("loadcell/port", port)
        logger.debug(f"로드셀 포트 저장: {port}")
    
    def load_loadcell_port(self) -> str:
        """마지막 사용한 로드셀 포트 불러오기"""
        port = self.settings.value("loadcell/port", "", type=str)
        logger.debug(f"로드셀 포트 불러오기: {port}")
        return port
    
    def save_loadcell_baudrate(self, baudrate: int):
        """마지막 사용한 로드셀 보드레이트 저장"""
        self.settings.setValue("loadcell/baudrate", baudrate)
    
    def load_loadcell_baudrate(self) -> int:
        """마지막 사용한 로드셀 보드레이트 불러오기"""
        return self.settings.value("loadcell/baudrate", 9600, type=int)
    
    # ========================================================================
    # Temp Controller 설정
    # ========================================================================
    
    def save_temp_port(self, port: str):
        """마지막 사용한 온도 제어기 포트 저장"""
        self.settings.setValue("temp/port", port)
        logger.debug(f"온도 제어기 포트 저장: {port}")
    
    def load_temp_port(self) -> str:
        """마지막 사용한 온도 제어기 포트 불러오기"""
        port = self.settings.value("temp/port", "", type=str)
        logger.debug(f"온도 제어기 포트 불러오기: {port}")
        return port
    
    def save_temp_baudrate(self, baudrate: int):
        """마지막 사용한 온도 제어기 보드레이트 저장"""
        self.settings.setValue("temp/baudrate", baudrate)
    
    def load_temp_baudrate(self) -> int:
        """마지막 사용한 온도 제어기 보드레이트 불러오기"""
        return self.settings.value("temp/baudrate", 9600, type=int)
    
    # ========================================================================
    # Monitoring 설정
    # ========================================================================
    
    def save_monitoring_hz(self, hz: int):
        """마지막 사용한 모니터링 주파수 저장"""
        self.settings.setValue("monitoring/hz", hz)
    
    def load_monitoring_hz(self) -> int:
        """마지막 사용한 모니터링 주파수 불러오기"""
        return self.settings.value("monitoring/hz", 10, type=int)
    
    # ========================================================================
    # Safety 설정
    # ========================================================================
    
    def save_displacement_limit(self, limit_mm: float):
        """변위 제한값 저장"""
        self.settings.setValue("safety/displacement_limit", limit_mm)
    
    def load_displacement_limit(self) -> float:
        """변위 제한값 불러오기"""
        return self.settings.value("safety/displacement_limit", 0.0, type=float)
    
    def save_force_limit(self, limit_n: float):
        """하중 제한값 저장"""
        self.settings.setValue("safety/force_limit", limit_n)
    
    def load_force_limit(self) -> float:
        """하중 제한값 불러오기"""
        return self.settings.value("safety/force_limit", 0.0, type=float)
    
    # ========================================================================
    # Window 설정
    # ========================================================================
    
    def save_window_geometry(self, geometry):
        """윈도우 위치/크기 저장"""
        self.settings.setValue("window/geometry", geometry)
    
    def load_window_geometry(self):
        """윈도우 위치/크기 불러오기"""
        return self.settings.value("window/geometry")
    
    def save_window_state(self, state):
        """윈도우 상태 저장 (최대화 등)"""
        self.settings.setValue("window/state", state)
    
    def load_window_state(self):
        """윈도우 상태 불러오기"""
        return self.settings.value("window/state")
    
    # ========================================================================
    # 유틸리티
    # ========================================================================
    
    def clear_all(self):
        """모든 설정 초기화"""
        self.settings.clear()
        logger.info("모든 설정이 초기화되었습니다.")
    
    def sync(self):
        """설정을 디스크에 즉시 저장"""
        self.settings.sync()
        logger.debug("설정 파일 동기화 완료")
