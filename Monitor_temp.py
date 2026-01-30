import logging
from PyQt5 import QtCore
from pymodbus.client.serial import ModbusSerialClient
from config import temp_cfg, monitor_cfg  # ===== 추가 =====

logger = logging.getLogger(__name__)


class TempWorker(QtCore.QObject):
    """
    QTimer 기반 온도 모니터링 워커
    """
    
    temp_ready = QtCore.pyqtSignal(list)

    def __init__(self, client: ModbusSerialClient, interval_ms: int):
        super().__init__()
        self.client = client
        self.interval_ms = interval_ms
        
        # ===== 수정: 매직 넘버 → config =====
        self.addr_list = [
            temp_cfg.CHANNEL_ADDRESSES[1]["PV"],  # ← 0x03E8 대신
            temp_cfg.CHANNEL_ADDRESSES[2]["PV"],  # ← 0x03EE 대신
            temp_cfg.CHANNEL_ADDRESSES[3]["PV"],  # ← 0x03F4 대신
            temp_cfg.CHANNEL_ADDRESSES[4]["PV"]   # ← 0x03FA 대신
        ]
        
        self.timer = None
        
        logger.info(f"TempWorker 생성됨 (주기: {interval_ms} ms)")

    @QtCore.pyqtSlot()
    def run(self):
        """타이머를 워커 스레드 내에서 생성"""
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.interval_ms)
        self.timer.timeout.connect(self._do_work)
        
        self.timer.start()
        logger.info(f"Temp 모니터링 타이머 시작")

    def _do_work(self):
        """타이머 콜백"""
        if not self.client or not self.client.is_socket_open():
            logger.debug("Temp 클라이언트 연결 없음 (스킵)")
            return
        
        current_temps = []
        try:
            for addr in self.addr_list:
                res = self.client.read_input_registers(
                    address=addr, 
                    count=1,
                    device_id=temp_cfg.DEFAULT_UNIT_ID  # ← 1 대신
                )
                if not res.isError():
                    val = res.registers[0]
                    current_temps.append(val)
                else:
                    current_temps.append(None)
            
            self.temp_ready.emit(current_temps)
        
        except Exception as e:
            logger.error(f"Temp Monitor Error: {e}", exc_info=True)

    @QtCore.pyqtSlot()
    def stop(self):
        """타이머 정지"""
        if self.timer and self.timer.isActive():
            self.timer.stop()
            logger.info("Temp 모니터링 타이머 정지")

    @QtCore.pyqtSlot(int)
    def set_interval(self, interval_ms: int):
        """타이머 주기 변경"""
        if not self.timer:
            logger.warning("타이머가 아직 생성되지 않았습니다.")
            return
        
        was_active = self.timer.isActive()
        
        if was_active:
            self.timer.stop()
        
        self.interval_ms = interval_ms
        self.timer.setInterval(interval_ms)
        
        if was_active:
            self.timer.start()
        
        logger.info(f"Temp 모니터링 주기 변경: {interval_ms} ms")


class TempMonitor(QtCore.QObject):
    """
    TempWorker를 별도의 QThread에서 실행하고 제어
    """
    start_worker = QtCore.pyqtSignal()
    stop_worker = QtCore.pyqtSignal()
    interval_changed = QtCore.pyqtSignal(int)

    def __init__(self, client, update_callback, interval_ms=500):
        super().__init__()
        
        # 스레드와 워커 생성
        self.thread = QtCore.QThread()
        self.worker = TempWorker(client, interval_ms)

        # 워커를 스레드로 이동
        self.worker.moveToThread(self.thread)

        # 시그널 연결
        self.thread.started.connect(self.worker.run)
        self.stop_worker.connect(self.worker.stop)
        self.interval_changed.connect(self.worker.set_interval)
        self.worker.temp_ready.connect(update_callback)

        # 스레드 정리
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # 스레드 시작
        self.thread.start()

        logger.info(f"TempMonitor 시작됨")

    def stop(self):
        """스레드를 안전하게 종료"""
        try:
            if hasattr(self, 'thread') and self.thread.isRunning():
                logger.info("TempMonitor: 스레드 종료 중...")
                
                self.stop_worker.emit()
                
                # ===== 수정: 매직 넘버 → config =====
                QtCore.QThread.msleep(monitor_cfg.THREAD_SLEEP_BEFORE_QUIT_MS)  # ← 100 대신
                
                self.thread.quit()
                
                # ===== 수정: 매직 넘버 → config =====
                if not self.thread.wait(monitor_cfg.THREAD_WAIT_TIMEOUT_MS):  # ← 2000 대신
                    logger.warning("Temp 스레드가 정상 종료되지 않았습니다. 강제 종료합니다.")
                    self.thread.terminate()
                    self.thread.wait()
                
            logger.info("TempMonitor 중지 완료")
        except Exception as e:
            logger.error(f"TempMonitor 정지 중 예외: {e}", exc_info=True)

    def update_interval(self, interval_ms: int):
        """Hz 변경 시 워커의 주기를 변경"""
        self.interval_changed.emit(interval_ms)
