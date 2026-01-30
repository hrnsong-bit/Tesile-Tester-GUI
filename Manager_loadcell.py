# Manager_loadcell.py
"""
Loadcell Manager
Controller와 Monitor를 통합 관리하고 DataHandler를 통해 데이터 전달
"""

from Controller_Loadcell import LoadcellService
from Monitor_loadcell import LoadcellMonitor
from config import loadcell_cfg, monitor_cfg
import logging
import time

logger = logging.getLogger(__name__)


class LoadcellManager:
    """
    Loadcell 장비의 Controller와 Monitor를 통합 관리
    """
    
    def __init__(self, data_handler):
        """
        Args:
            data_handler: DataHandler 인스턴스 (데이터 처리 위임)
        """
        self.data_handler = data_handler
        self.controller = None
        self.monitor = None
        self.start_time = None
        
        logger.info("LoadcellManager 초기화 완료")
    
    def start_service(self, serial_port, interval_ms=None):
        """
        Loadcell 서비스 시작 (연결 성공 후 호출)
        
        Args:
            serial_port: serial.Serial 인스턴스 (Main.py에서 생성)
            interval_ms: 모니터링 간격 (기본값: config에서 로드)
        """
        if interval_ms is None:
            interval_ms = monitor_cfg.DEFAULT_INTERVAL_MS
            
        try:
            # Controller 생성 (Serial 객체 주입)
            self.controller = LoadcellService(ser=serial_port)
            self.start_time = time.time()
            
            logger.info("LoadcellService 생성 완료")
            
            # Monitor 생성 및 시작
            self.monitor = LoadcellMonitor(
                serial_port, 
                self._on_data_received,  # 콜백
                interval_ms
            )
            
            logger.info(f"LoadcellManager 서비스 시작 (Interval: {interval_ms}ms)")
            return True
        
        except Exception as e:
            logger.error(f"LoadcellManager 서비스 시작 실패: {e}", exc_info=True)
            return False
    
    def stop_service(self):
        """Loadcell 서비스 중지 (연결 해제 시 호출)"""
        try:
            if self.monitor:
                self.monitor.stop()
                self.monitor = None
                logger.info("Loadcell Monitor 중지 완료")
            
            # Controller 정리 (Serial 객체는 Main.py가 닫음)
            self.controller = None
            
            logger.info("LoadcellManager 서비스 중지 완료")
        
        except Exception as e:
            logger.error(f"LoadcellManager 서비스 중지 실패: {e}", exc_info=True)
    
    def _on_data_received(self, norm_x100k: float):
        """
        Monitor로부터 데이터를 받아 DataHandler로 전달
        
        Args:
            norm_x100k: 정규화된 하중 값 (N)
        """
        if not self.start_time:
            return
        
        try:
            # DataHandler의 update_loadcell_value 호출
            self.data_handler.update_loadcell_value(norm_x100k)
        
        except Exception as e:
            logger.error(f"Loadcell 데이터 전달 실패: {e}", exc_info=True)
    
    # ========================================================================
    # Controller 래핑 메서드 (자주 사용되는 기능)
    # ========================================================================
    
    def zero_calibration(self):
        """영점 보정"""
        if not self.controller:
            logger.error("LoadcellService가 연결되지 않았습니다.")
            return False
        
        try:
            self.controller.zero_position()
            logger.info("Loadcell 영점 보정 성공")
            return True
        except Exception as e:
            logger.error(f"Loadcell 영점 보정 오류: {e}", exc_info=True)
            return False
    
    def is_connected(self):
        """연결 상태 확인"""
        return (self.controller is not None and 
                self.controller.ser is not None and 
                self.controller.ser.is_open)
    
    def is_monitoring(self):
        """모니터링 상태 확인"""
        return (self.monitor is not None and 
                hasattr(self.monitor, 'worker') and 
                self.monitor.worker._running)
