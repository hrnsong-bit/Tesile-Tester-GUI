# Manager_motor.py
"""
Motor Manager
Controller와 Monitor를 통합 관리하고 DataHandler를 통해 데이터 전달
"""

from Controller_motor import MotorService
from Monitor_motor import MotorMonitor
from config import motor_cfg, monitor_cfg
import logging
import time

logger = logging.getLogger(__name__)


class MotorManager:
    """
    Motor 장비의 Controller와 Monitor를 통합 관리
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
        
        logger.info("MotorManager 초기화 완료")
    
    def start_service(self, client, unit_id=None, interval_ms=None):
        """
        Motor 서비스 시작 (연결 성공 후 호출)
        
        Args:
            client: ModbusSerialClient 인스턴스
            unit_id: Modbus Unit ID (기본값: config에서 로드)
            interval_ms: 모니터링 간격 (기본값: config에서 로드)
        """
        if unit_id is None:
            unit_id = motor_cfg.DEFAULT_UNIT_ID
        if interval_ms is None:
            interval_ms = monitor_cfg.DEFAULT_INTERVAL_MS
            
        try:
            # Controller 생성
            self.controller = MotorService(client, unit_id=unit_id)
            self.start_time = time.time()
            
            # Monitor 생성 및 시작
            self.monitor = MotorMonitor(
                client, 
                self._on_data_received,  # 콜백
                interval_ms
            )
            
            logger.info(f"MotorManager 서비스 시작 (Unit ID: {unit_id}, Interval: {interval_ms}ms)")
            return True
        
        except Exception as e:
            logger.error(f"MotorManager 서비스 시작 실패: {e}", exc_info=True)
            return False
    
    def stop_service(self):
        """Motor 서비스 중지 (연결 해제 시 호출)"""
        try:
            if self.monitor:
                self.monitor.stop()
                self.monitor = None
                logger.info("Motor Monitor 중지 완료")
            
            # Controller 정리
            self.controller = None
            
            logger.info("MotorManager 서비스 중지 완료")
        
        except Exception as e:
            logger.error(f"MotorManager 서비스 중지 실패: {e}", exc_info=True)
    
    def _on_data_received(self, displacement_um: float):
        """
        Monitor로부터 데이터를 받아 DataHandler로 전달
        
        Args:
            displacement_um: 변위 (um)
        """
        if not self.start_time:
            return
        
        try:
            # DataHandler의 update_motor_position 호출
            self.data_handler.update_motor_position(displacement_um)
        
        except Exception as e:
            logger.error(f"Motor 데이터 전달 실패: {e}")
    
    # ========================================================================
    # 상태 확인 메서드
    # ========================================================================
    
    def is_connected(self):
        """연결 상태 확인"""
        return self.controller is not None
    
    def is_monitoring(self):
        """모니터링 상태 확인"""
        return (self.monitor is not None and 
                hasattr(self.monitor, 'worker') and 
                self.monitor.worker._running)
