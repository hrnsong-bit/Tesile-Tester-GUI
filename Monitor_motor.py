# Monitor_motor.py
import time
import logging
from PyQt5 import QtCore
from pymodbus.client.serial import ModbusSerialClient

logger = logging.getLogger(__name__)

class MotorWorker(QtCore.QObject):
    """
    QTimer 기반 모터 모니터링 워커
    무한 루프 대신 타이머를 사용하여 정확한 주기 제어
    """
    
    data_ready = QtCore.pyqtSignal(float)

    def __init__(self, client: ModbusSerialClient, unit_id: int, interval_ms: int):
        super().__init__()
        self.client = client
        self.unit_id = unit_id
        self.interval_ms = interval_ms
        
        # QTimer 생성
        self.timer = QtCore.QTimer()
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self._do_work)
        
        logger.info(f"MotorWorker 생성됨 (Unit ID: {unit_id}, 주기: {interval_ms} ms)")

    @QtCore.pyqtSlot()
    def run(self):
        """타이머 시작"""
        self.timer.start()
        logger.info("Motor 모니터링 타이머 시작")

    def _do_work(self):
        """타이머 콜백 - 매 interval마다 호출됨"""
        try:
            if not self.client or not self.client.is_socket_open():
                logger.debug("클라이언트 연결 없음 (스킵)")
                return

            # Modbus 읽기
            result_pos = self.client.read_holding_registers(
                address=117, 
                count=2,
                device_id=self.unit_id
            )
            regs = getattr(result_pos, "registers", None)

            if result_pos.isError() or regs is None or len(regs) != 2:
                logger.debug(f"현재 위치 읽기 실패: {result_pos}")
                return

            # 데이터 파싱
            reg126, reg127 = regs
            r126_hi = (reg126 >> 8) & 0xFF
            r126_lo =  reg126       & 0xFF
            r127_hi = (reg127 >> 8) & 0xFF
            r127_lo =  reg127       & 0xFF

            position = ((r127_hi << 24) |
                        (r127_lo << 16) |
                        (r126_hi << 8)  |
                        (r126_lo))

            if position & 0x80000000:
                position -= 0x100000000

            displacement_um = - (position / 10000.0) * 1000.0

            # 메인 스레드로 데이터 전송
            self.data_ready.emit(displacement_um)

        except Exception as e:
            logger.error(f"모터 모니터링 워커 예외: {e}", exc_info=True)
                
    @QtCore.pyqtSlot()
    def stop(self):
        """타이머 정지"""
        if self.timer.isActive():
            self.timer.stop()
            logger.info("Motor 모니터링 타이머 정지")

    @QtCore.pyqtSlot(int)
    def set_interval(self, interval_ms: int):
        """타이머 주기 변경"""
        was_active = self.timer.isActive()
        
        if was_active:
            self.timer.stop()
        
        self.interval_ms = interval_ms
        self.timer.setInterval(interval_ms)
        
        if was_active:
            self.timer.start()
        
        logger.info(f"Motor 모니터링 주기 변경: {interval_ms} ms")


class MotorMonitor(QtCore.QObject):
    """
    MotorWorker를 별도의 QThread에서 실행하고 제어하는 컨트롤러 클래스.
    """
    start_worker = QtCore.pyqtSignal()
    stop_worker = QtCore.pyqtSignal()
    interval_changed = QtCore.pyqtSignal(int)

    def __init__(self, client: ModbusSerialClient, update_callback, interval_ms=100, unit_id=1):
        super().__init__()
        
        # 스레드와 워커 생성
        self.thread = QtCore.QThread()
        self.worker = MotorWorker(client, unit_id, interval_ms)

        # 워커를 스레드로 이동
        self.worker.moveToThread(self.thread)

        # 시그널 연결
        self.start_worker.connect(self.worker.run)
        self.stop_worker.connect(self.worker.stop)
        self.interval_changed.connect(self.worker.set_interval)
        self.worker.data_ready.connect(update_callback)

        # 스레드 정리
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # 스레드 시작
        self.thread.start()
        self.start_worker.emit()

        logger.info(f"MotorMonitor 시작됨 (스레드 ID: {int(self.thread.currentThreadId())})")

    def stop(self):
        """스레드를 안전하게 종료"""
        try:
            if hasattr(self, 'thread') and self.thread.isRunning():
                logger.info("MotorMonitor: 스레드 종료 중...")
                
                # 1. 워커의 타이머 정지
                self.stop_worker.emit()
                
                # 2. 스레드의 이벤트 루프 종료
                self.thread.quit()
                
                # 3. 최대 2초 대기
                if not self.thread.wait(2000):
                    logger.warning("Motor 스레드가 정상 종료되지 않았습니다. 강제 종료합니다.")
                    self.thread.terminate()
                    self.thread.wait()
                
            logger.info("MotorMonitor 중지 완료")
        except Exception as e:
            logger.error(f"MotorMonitor 정지 중 예외: {e}", exc_info=True)

    def update_interval(self, interval_ms: int):
        """Hz 변경 시 워커의 주기를 변경"""
        self.interval_changed.emit(interval_ms)
