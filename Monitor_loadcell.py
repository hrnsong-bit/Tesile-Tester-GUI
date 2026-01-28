# Monitor_loadcell.py
import time
import serial
import logging
from PyQt5 import QtCore

logger = logging.getLogger(__name__)

_FULLSCALE = 2147483647  # 2^31 - 1 (sint32 max)

# ===================================================================
# 1. Helper Functions (파일 스코프의 헬퍼 함수)
# ===================================================================

def _to_s32_be(b4: bytes) -> int:
    """빅엔디언 4바이트 → 부호 32비트 정수"""
    if len(b4) != 4:
        return 0
    u = (b4[0] << 24) | (b4[1] << 16) | (b4[2] << 8) | b4[3]
    return u - 0x100000000 if (u & 0x80000000) else u

def _read_until_crlf(ser, max_wait=1.5, idle_gap=0.10) -> bytes:
    """CRLF(0x0D0A)까지 읽기 / idle_gap 동안 무수신 시 종료"""
    t0 = time.time()
    last = t0
    buf = bytearray()
    while time.time() - t0 < max_wait:
        n = ser.in_waiting or 1
        chunk = ser.read(n)
        if chunk:
            buf += chunk
            last = time.time()
            if len(buf) >= 2 and buf[-2:] == b"\r\n":
                break
        else:
            if len(buf) and (time.time() - last) >= idle_gap:
                break
    return bytes(buf)

def _msv_once_via_serial(ser: serial.Serial) -> tuple[bool, int, bytes]:
    """
    [워커 스레드에서 호출됨]
    시리얼 포트를 통해 단일 측정(MSV)을 수행합니다.
    """
    if not ser or not ser.is_open:
        logger.error("ERR: Serial 포트가 열려 있지 않습니다.")
        return (False, 0, b"")

    try:
        ser.reset_input_buffer()
        # 1) 주소 선택
        ser.write(b";S21;")
        ser.flush()
        # [중요] time.sleep은 워커 스레드에서만 사용해야 합니다.
        time.sleep(0.02) 

        # 2) 단일 측정 명령
        ser.write(b";MSV?;")
        ser.flush()

        raw = _read_until_crlf(ser)

        if len(raw) < 4:
            logger.warning("응답이 너무 짧습니다.")
            return (False, 0, raw)

        first4 = raw[:4]
        counts = _to_s32_be(first4)
        return (True, counts, raw)

    except Exception as e:
        logger.error(f"_msv_once_via_serial 예외 발생: {e}")
        return (False, 0, b"")

# ===================================================================
# 2. Worker (별도 스레드에서 실행될 실제 통신 담당)
# ===================================================================
class LoadcellWorker(QtCore.QObject):
    """
    별도의 스레드에서 시리얼 통신을 실행하는 워커.
    시간이 오래 걸리는 I/O 작업을 GUI 스레드와 분리합니다.
    """
    
    # 데이터가 준비되었을 때 GUI 스레드로 보낼 시그널 (norm_x100k 값)
    data_ready = QtCore.pyqtSignal(float)

    def __init__(self, ser: serial.Serial, interval_ms: int):
        super().__init__()
        self.ser = ser
        self.interval_ms = interval_ms
        self._running = False
        logger.info(f"워커 생성됨 (주기: {interval_ms} ms)")

    @QtCore.pyqtSlot()
    def run(self):
        """워커 스레드의 메인 루프. _running 플래그가 True인 동안 반복."""
        self._running = True
        logger.info("워커 스레드 시작.")
        
        while self._running:
            loop_start_time = time.time()
            
            try:
                # --- 기존 read_and_update 로직 시작 ---
                if not self.ser or not self.ser.is_open:
                    time.sleep(0.5) # 연결 대기
                    continue
                    
                ok, counts, raw = _msv_once_via_serial(self.ser)
                if not ok:
                    logger.debug("MSV 읽기 실패 (skip)")
                    continue

                normalized = counts / float(_FULLSCALE)
                norm_x100k = normalized * 100000.0 * -0.0098
                logger.debug(f"변환 결과: counts={counts}, normalized={normalized:.6f}, scaled={norm_x100k:.3f}")
                # --- 기존 로직 끝 ---

                # [중요] 데이터를 메인 스레드로 전송
                self.data_ready.emit(norm_x100k)

            except Exception as e:
                logger.error(f"모니터링 스레드 예외: {e}")

            # --- 주기 맞추기 ---
            elapsed_sec = time.time() - loop_start_time
            sleep_sec = (self.interval_ms / 1000.0) - elapsed_sec
            
            if sleep_sec > 0:
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
# 3. Monitor (GUI 스레드에서 워커를 제어하는 컨트롤러)
# ===================================================================

#  ========== 수정된 부분: QObject 상속 ==========
class LoadcellMonitor(QtCore.QObject):
    """
    LoadcellWorker를 별도의 QThread에서 실행하고 제어하는 컨트롤러 클래스.
    Main.py는 이 클래스만 알고 있으면 됩니다.
    """
    # 워커 스레드에게 "시작하라"고 보낼 시그널
    start_worker = QtCore.pyqtSignal()
    # 워커 스레드에게 "중지하라"고 보낼 시그널
    stop_worker = QtCore.pyqtSignal()
    # 워커 스레드에게 "주기 변경하라"고 보낼 시그널
    interval_changed = QtCore.pyqtSignal(int)

    def __init__(self, ser: serial.Serial, update_callback, interval_ms=100):
        #  ========== 수정된 부분: super() 호출 ==========
        super().__init__()
        
        self.thread = QtCore.QThread()
        self.worker = LoadcellWorker(ser, interval_ms)

        self.worker.moveToThread(self.thread)

        # --- 시그널 연결 ---
        self.start_worker.connect(self.worker.run)
        self.stop_worker.connect(self.worker.stop)
        self.interval_changed.connect(self.worker.set_interval)

        # [중요] 워커의 data_ready 시그널을 update_callback에 직접 연결
        self.worker.data_ready.connect(update_callback)

        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        self.start_worker.emit()

        logger.info(f"모니터 컨트롤러 시작됨 (스레드 ID: {int(self.thread.currentThreadId())})")

    def stop(self):
        """스레드를 안전하게 종료시킵니다."""
        try:
            if hasattr(self, 'thread') and self.thread.isRunning():
                logger.info("모니터 컨트롤러: 스레드 종료 중...")
                self.stop_worker.emit()
                self.thread.quit()
                self.thread.wait(1000)
            logger.info("모니터 컨트롤러 중지됨.")
        except Exception as e:
            logger.error(f"모니터 정지 중 예외: {e}")

    def update_interval(self, interval_ms: int):
        """Hz 변경 시, 실행 중인 워커의 주기를 변경합니다."""
        self.interval_changed.emit(interval_ms)