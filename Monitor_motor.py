# Monitor_motor.py
import time
import logging
from PyQt5 import QtCore
from pymodbus.client.serial import ModbusSerialClient

logger = logging.getLogger(__name__)

# ===================================================================
# 1. Worker (별도 스레드에서 실행될 실제 통신 담당)
# ===================================================================
class MotorWorker(QtCore.QObject):
    """
    별도의 스레드에서 Modbus 통신을 실행하는 워커.
    시간이 오래 걸리는 I/O 작업을 GUI 스레드와 분리합니다.
    """
    
    # 데이터가 준비되었을 때 GUI 스레드로 보낼 시그널 (displacement_um 값)
    data_ready = QtCore.pyqtSignal(float)

    def __init__(self, client: ModbusSerialClient, interval_ms: int):
        super().__init__()
        self.client = client
        self.interval_ms = interval_ms
        self._running = False
        logger.info(f"워커 생성됨 (주기: {interval_ms} ms)")

    @QtCore.pyqtSlot()
    def run(self):
        """워커 스레드의 메인 루프. _running 플래그가 True인 동안 반복."""
        self.loop_timer = QtCore.QTimer()
        self.loop_timer.setInterval(self.interval_ms)
        self.loop_timer.timeout.connect(self._do_work)
        self.loop_timer.start()
    
    def _do_work(self):
        if not self._running:
            self.loop_timer.stop()
            return
        
        while self._running:
            loop_start_time = time.time()
            
            try:
                # --- 기존 read_and_update 로직 시작 ---
                if not self.client or not self.client.is_socket_open():
                    # 스레드가 실행 중이므로 잠시 대기 후 다음 루프 시도
                    time.sleep(0.5) 
                    continue

                result_pos = self.client.read_holding_registers(address=117, count=2)
                regs = getattr(result_pos, "registers", None)

                if result_pos.isError() or regs is None or len(regs) != 2:
                    logger.warning(f"현재 위치 읽기 실패: {result_pos}")
                    position = 0
                else:
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
                # --- 기존 로직 끝 ---

                # [중요] 데이터를 메인 스레드로 전송
                self.data_ready.emit(displacement_um)

            except Exception as e:
                logger.error(f"모니터링 스레드 예외: {e}")

            # --- 주기 맞추기 ---
            elapsed_sec = time.time() - loop_start_time
            sleep_sec = (self.interval_ms / 1000.0) - elapsed_sec
            
            if sleep_sec > 0:
                # time.sleep은 블로킹이지만, 여긴 워커 스레드이므로 GUI에 영향 없음
                time.sleep(sleep_sec) 
                
    @QtCore.pyqtSlot()
    def stop(self):
        """메인 루프를 중지시킵니다."""
        logger.info("워커 스레드 중지 요청.")
        self._running = False

    @QtCore.pyqtSlot(int)
    def set_interval(self, interval_ms: int):
        """Hz 설정 변경 시 호출되어 주기를 업데이트합니다."""
        logger.info(f"워커 주기 변경: {self.interval_ms} -> {interval_ms} ms")
        self.interval_ms = interval_ms

# ===================================================================
# 2. Monitor (GUI 스레드에서 워커를 제어하는 컨트롤러)
# ===================================================================

#  ========== QObject 상속 ==========
class MotorMonitor(QtCore.QObject):
    """
    MotorWorker를 별도의 QThread에서 실행하고 제어하는 컨트롤러 클래스.
    Main.py는 이 클래스만 알고 있으면 됩니다.
    """
    # 워커 스레드에게 "시작하라"고 보낼 시그널
    start_worker = QtCore.pyqtSignal()
    # 워커 스레드에게 "중지하라"고 보낼 시그널
    stop_worker = QtCore.pyqtSignal()
    # 워커 스레드에게 "주기 변경하라"고 보낼 시그널
    interval_changed = QtCore.pyqtSignal(int)

    def __init__(self, client: ModbusSerialClient, update_callback, interval_ms=100):
        #  ========== super() 호출 ==========
        super().__init__() 
        
        # 1. 스레드와 워커 객체 생성
        self.thread = QtCore.QThread()
        self.worker = MotorWorker(client, interval_ms)

        # 2. 워커를 스레드로 이동
        self.worker.moveToThread(self.thread)

        # 3. 시그널 연결
        # 3a. Main -> Monitor -> Worker (제어)
        self.start_worker.connect(self.worker.run)
        self.stop_worker.connect(self.worker.stop)
        self.interval_changed.connect(self.worker.set_interval)

        # 3b. Worker -> Main (데이터)
        #    [중요] 워커의 data_ready 시그널을 Main.py가 넘겨준 
        #    update_callback(Data_Handler.update_motor_position)에 직접 연결
        self.worker.data_ready.connect(update_callback)

        # 3c. 스레드 종료 시 자가 정리
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # 4. 스레드 시작
        self.thread.start()
        
        # 5. 워커의 run() 함수 실행
        self.start_worker.emit()

        logger.info(f"모니터 컨트롤러 시작됨 (스레드 ID: {int(self.thread.currentThreadId())})")

    def stop(self):
        """스레드를 안전하게 종료시킵니다."""
        try:
            if hasattr(self, 'thread') and self.thread.isRunning():
                logger.info("모니터 컨트롤러: 스레드 종료 중...")
                # 1. 워커의 while 루프 중지
                self.stop_worker.emit()
                # 2. 스레드의 이벤트 루프 종료
                self.thread.quit()
                # 3. 스레드가 완전히 끝날 때까지 최대 1초 대기
                self.thread.wait(1000)
            logger.info("모니터 컨트롤러 중지됨.")
        except Exception as e:
            logger.error(f"모니터 정지 중 예외: {e}")

    def update_interval(self, interval_ms: int):
        """Hz 변경 시, 실행 중인 워커의 주기를 변경합니다."""
        self.interval_changed.emit(interval_ms)