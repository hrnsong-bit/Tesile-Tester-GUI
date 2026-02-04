import time
import logging
from PyQt5 import QtCore
from pymodbus.client.serial import ModbusSerialClient
from config import motor_cfg, monitor_cfg

logger = logging.getLogger(__name__)


class MotorWorker(QtCore.QObject):
    """
    QTimer 기반 모터 모니터링 워커
    """
    
    data_ready = QtCore.pyqtSignal(float)

    def __init__(self, client: ModbusSerialClient, unit_id: int, interval_ms: int):
        super().__init__()
        self.client = client
        self.unit_id = unit_id
        self.interval_ms = interval_ms
        self._running = False
        
        # ===== 중요: Timer는 run()에서 생성해야 함 =====
        self.timer = None
        
        logger.info(f"MotorWorker 생성됨 (Unit ID: {unit_id}, 주기: {interval_ms} ms)")

    @QtCore.pyqtSlot()
    def run(self):
        """타이머 시작 - 워커 스레드에서 실행됨"""
        # ===== Timer를 현재 스레드(워커 스레드)에서 생성 =====
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.interval_ms)
        self.timer.timeout.connect(self._do_work)
        
        self._running = True
        self.timer.start()
        logger.info(f"Motor 모니터링 타이머 시작됨 (Thread ID: {int(QtCore.QThread.currentThreadId())})")

    def _do_work(self):
        """타이머 콜백 - 매 interval마다 호출됨"""
        if not self._running:
            return
            
        try:
            if not self.client or not self.client.is_socket_open():
                logger.debug("클라이언트 연결 없음 (스킵)")
                return

            # 위치 레지스터 읽기
            result_pos = self.client.read_holding_registers(
                address=motor_cfg.REG_POSITION_HI,
                count=2,
                device_id=self.unit_id
            )
            
            if result_pos.isError():
                logger.debug(f"현재 위치 읽기 실패: {result_pos}")
                return
                
            regs = getattr(result_pos, "registers", None)
            if regs is None or len(regs) != 2:
                logger.debug(f"레지스터 데이터 없음: {regs}")
                return

            # 32비트 위치 값 조합
            reg126, reg127 = regs
            r126_hi = (reg126 >> motor_cfg.BYTE_SHIFT) & motor_cfg.BYTE_MASK_LO
            r126_lo = reg126 & motor_cfg.BYTE_MASK_LO
            r127_hi = (reg127 >> motor_cfg.BYTE_SHIFT) & motor_cfg.BYTE_MASK_LO
            r127_lo = reg127 & motor_cfg.BYTE_MASK_LO

            position = ((r127_hi << 24) |
                        (r127_lo << 16) |
                        (r126_hi << motor_cfg.BYTE_SHIFT) |
                        (r126_lo))

            # 부호 있는 32비트로 변환
            if position & motor_cfg.SINT32_SIGN_BIT:
                position -= motor_cfg.SINT32_OVERFLOW

            # um로 변환
            displacement_um = (
                motor_cfg.POSITION_SIGN_INVERT *
                (position / motor_cfg.POSITION_SCALE_FACTOR) *
                motor_cfg.UM_PER_MM
            )

            # 메인 스레드로 데이터 전송
            self.data_ready.emit(displacement_um)

        except Exception as e:
            logger.error(f"모터 모니터링 워커 예외: {e}", exc_info=True)
                
    @QtCore.pyqtSlot()
    def stop(self):
        """타이머 정지"""
        self._running = False
        if self.timer and self.timer.isActive():
            self.timer.stop()
            logger.info("Motor 모니터링 타이머 정지")

    @QtCore.pyqtSlot(int)
    def set_interval(self, interval_ms: int):
        """타이머 주기 변경"""
        if not self.timer:
            logger.warning("Timer가 아직 생성되지 않았습니다.")
            return
            
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
    MotorWorker를 별도의 QThread에서 실행하고 제어
    """
    start_worker = QtCore.pyqtSignal()
    stop_worker = QtCore.pyqtSignal()
    interval_changed = QtCore.pyqtSignal(int)

    def __init__(self, client: ModbusSerialClient, update_callback, interval_ms=100, unit_id=1):
        super().__init__()
        
        # 스레드 생성 및 시작
        self.thread = QtCore.QThread()
        self.thread.start()
        
        # 워커 생성 (메인 스레드에서)
        self.worker = MotorWorker(client, unit_id, interval_ms)

        # 워커를 워커 스레드로 이동
        self.worker.moveToThread(self.thread)

        # ===== 중요: 스레드의 started 시그널에 연결 =====
        self.thread.started.connect(self.worker.run)
        
        # 시그널 연결
        self.start_worker.connect(self.worker.run)
        self.stop_worker.connect(self.worker.stop)
        self.interval_changed.connect(self.worker.set_interval)
        self.worker.data_ready.connect(update_callback)

        # 스레드 정리
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        logger.info(f"MotorMonitor 시작됨 (Main Thread ID: {int(QtCore.QThread.currentThreadId())})")

    def stop(self):
        """스레드를 안전하게 종료"""
        try:
            if hasattr(self, 'thread') and self.thread.isRunning():
                logger.info("MotorMonitor: 스레드 종료 중...")
                
                # 1. 워커의 타이머 정지
                self.stop_worker.emit()
                
                # 2. 약간의 대기
                QtCore.QThread.msleep(100)
                
                # 3. 스레드의 이벤트 루프 종료
                self.thread.quit()
                
                if not self.thread.wait(monitor_cfg.THREAD_WAIT_TIMEOUT_MS):
                    logger.warning("Motor 스레드가 정상 종료되지 않았습니다. 강제 종료합니다.")
                    self.thread.terminate()
                    self.thread.wait()
                
            logger.info("MotorMonitor 중지 완료")
        except Exception as e:
            logger.error(f"MotorMonitor 정지 중 예외: {e}", exc_info=True)

    def update_interval(self, interval_ms: int):
        """Hz 변경 시 워커의 주기를 변경"""
        self.interval_changed.emit(interval_ms)