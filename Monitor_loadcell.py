import time
import serial
import logging
from PyQt5 import QtCore
from config import loadcell_cfg, monitor_cfg  # ===== 추가 =====

logger = logging.getLogger(__name__)

_FULLSCALE = loadcell_cfg.FULLSCALE


def _hex_dump(data: bytes, maxlen=256):
    s = " ".join(f"{b:02X}" for b in data[:maxlen])
    if len(data) > maxlen:
        s += f" …(+{len(data)-maxlen}B)"
    return s


def _to_s32_be(b4: bytes) -> int:
    """빅엔디언 4바이트 → 부호 있는 32비트 정수"""
    if len(b4) != 4:
        return 0
    u = (b4[0] << 24) | (b4[1] << 16) | (b4[2] << 8) | b4[3]
    return u - 0x100000000 if (u & 0x80000000) else u


def _read_until_crlf(ser, max_wait=1.5, idle_gap=0.10) -> bytes:
    """CRLF(0x0D0A)까지 읽기"""
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
            elif n == 0:
                time.sleep(0.01)
    return bytes(buf)


def _msv_once_via_serial(ser: serial.Serial) -> tuple[bool, int, bytes]:
    """시리얼 포트를 통해 단일 측정(MSV) 수행"""
    if not ser or not ser.is_open:
        logger.error("Serial 포트가 열려 있지 않습니다.")
        return (False, 0, b"")

    try:
        ser.reset_input_buffer()
        
        # ===== 수정: 매직 넘버 → config =====
        # 주소 선택 명령 생성
        addr_cmd = loadcell_cfg.CMD_SELECT_ADDRESS.format(
            address=loadcell_cfg.DEVICE_ADDRESS
        )
        frame = f"{loadcell_cfg.FRAME_START}{addr_cmd}{loadcell_cfg.FRAME_END}"
        ser.write(frame.encode('ascii'))  # ;S21; 대신
        ser.flush()
        time.sleep(0.02)

        # 단일 측정 명령
        measure_frame = (
            f"{loadcell_cfg.FRAME_START}"
            f"{loadcell_cfg.CMD_SINGLE_MEASURE}"
            f"{loadcell_cfg.FRAME_END}"
        )
        ser.write(measure_frame.encode('ascii'))  # ;MSV?; 대신
        ser.flush()

        raw = _read_until_crlf(ser)

        if len(raw) < 4:
            logger.debug("응답이 너무 짧습니다.")
            return (False, 0, raw)

        first4 = raw[:4]
        counts = _to_s32_be(first4)
        return (True, counts, raw)

    except Exception as e:
        logger.error(f"_msv_once_via_serial 예외: {e}")
        return (False, 0, b"")


class LoadcellWorker(QtCore.QObject):
    """
    QTimer 기반 로드셀 모니터링 워커
    """
    
    data_ready = QtCore.pyqtSignal(float)

    def __init__(self, ser: serial.Serial, interval_ms: int):
        super().__init__()
        self.ser = ser
        self.interval_ms = interval_ms
        self.timer = None
        
        logger.info(f"LoadcellWorker 생성됨 (주기: {interval_ms} ms)")

    @QtCore.pyqtSlot()
    def run(self):
        """워커 스레드 시작 시 호출"""
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.interval_ms)
        self.timer.timeout.connect(self._do_work)
        self.timer.start()
        
        logger.info(f"Loadcell 모니터링 타이머 시작")

    def _do_work(self):
        """타이머 콜백"""
        try:
            if not self.ser or not self.ser.is_open:
                logger.debug("Serial 포트 연결 없음 (스킵)")
                return
                
            ok, counts, raw = _msv_once_via_serial(self.ser)
            if not ok:
                logger.debug("MSV 읽기 실패 (skip)")
                return

            # ===== 수정: 매직 넘버 → config =====
            normalized = counts / float(_FULLSCALE)
            norm_x100k = (
                normalized * 
                loadcell_cfg.NORMALIZATION_FACTOR *  # ← 100000.0 대신
                loadcell_cfg.GRAVITY_FACTOR          # ← -0.0098 대신
            )
            
            self.data_ready.emit(norm_x100k)

        except Exception as e:
            logger.error(f"로드셀 모니터링 워커 예외: {e}", exc_info=True)

    @QtCore.pyqtSlot()
    def stop(self):
        """타이머 정지"""
        if self.timer and self.timer.isActive():
            self.timer.stop()
            logger.info("Loadcell 모니터링 타이머 정지")

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
        
        logger.info(f"Loadcell 모니터링 주기 변경: {interval_ms} ms")


class LoadcellMonitor(QtCore.QObject):
    """
    LoadcellWorker를 별도의 QThread에서 실행하고 제어
    """
    start_worker = QtCore.pyqtSignal()
    stop_worker = QtCore.pyqtSignal()
    interval_changed = QtCore.pyqtSignal(int)

    def __init__(self, ser: serial.Serial, update_callback, interval_ms=100):
        super().__init__()
        
        # 스레드와 워커 생성
        self.thread = QtCore.QThread()
        self.worker = LoadcellWorker(ser, interval_ms)

        # 워커를 스레드로 이동
        self.worker.moveToThread(self.thread)

        # 시그널 연결
        self.thread.started.connect(self.worker.run)
        self.stop_worker.connect(self.worker.stop)
        self.interval_changed.connect(self.worker.set_interval)
        self.worker.data_ready.connect(update_callback)

        # 스레드 정리
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # 스레드 시작
        self.thread.start()

        logger.info(f"LoadcellMonitor 시작됨")

    def stop(self):
        """스레드를 안전하게 종료"""
        try:
            if hasattr(self, 'thread') and self.thread.isRunning():
                logger.info("LoadcellMonitor: 스레드 종료 중...")
                
                # 1. 워커의 타이머 정지
                self.stop_worker.emit()
                
                # ===== 수정: 매직 넘버 → config =====
                QtCore.QThread.msleep(monitor_cfg.THREAD_SLEEP_BEFORE_QUIT_MS)  # ← 100 대신
                
                # 2. 스레드의 이벤트 루프 종료
                self.thread.quit()
                
                # ===== 수정: 매직 넘버 → config =====
                if not self.thread.wait(monitor_cfg.THREAD_WAIT_TIMEOUT_MS):  # ← 2000 대신
                    logger.warning("Loadcell 스레드가 정상 종료되지 않았습니다. 강제 종료합니다.")
                    self.thread.terminate()
                    self.thread.wait()
                
            logger.info("LoadcellMonitor 중지 완료")
        except Exception as e:
            logger.error(f"LoadcellMonitor 정지 중 예외: {e}", exc_info=True)

    def update_interval(self, interval_ms: int):
        """Hz 변경 시 워커의 주기를 변경"""
        self.interval_changed.emit(interval_ms)
