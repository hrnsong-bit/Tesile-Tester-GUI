# Controller_Loadcell.py
import time
import serial
import re
import logging

logger = logging.getLogger(__name__)

# ─────────────────────────────
# 헬퍼 함수들 (비공개 메서드로 변경)
# ─────────────────────────────
def _hex_dump(data: bytes, maxlen=256):
    s = " ".join(f"{b:02X}" for b in data[:maxlen])
    if len(data) > maxlen:
        s += f" …(+{len(data)-maxlen}B)"
    return s

def _extract_status_code_from_ascii(ascii_text: str):
    m = re.search(r"(?<!\d)([-+]?\d+)(?!\d)", ascii_text)
    return int(m.group(1)) if m else None

def _interpret_status(code: int, what: str) -> str:
    if code == 0:
        return f"[{what}] status=0 → OK (명령 수락)"
    return f"[{what}] status={code} → 매뉴얼 확인 필요"


class LoadcellService:
    def __init__(self):
        self.ser = serial.Serial()
        logger.info("초기화됨")

    def connect(self, port, baudrate, parity='E', bytesize=8, stopbits=1, timeout=1.0) -> bool:
        """지정된 포트와 설정으로 시리얼 연결을 시도합니다."""
        if self.ser and self.ser.is_open:
            logger.info(f"이미 연결되어 있습니다: {self.ser.port}")
            return True
        try:
            self.ser.port = port
            self.ser.baudrate = baudrate
            self.ser.parity = parity
            self.ser.bytesize = bytesize
            self.ser.stopbits = stopbits
            self.ser.timeout = timeout
            self.ser.open()
            logger.info(f"연결 성공: {port} @ {baudrate}")
            return True
        except Exception as e:
            logger.error(f"연결 실패: {e}")
            self.ser.close() # 실패 시 확실히 닫음
            return False

    def disconnect(self):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
                logger.info("연결 해제됨")
        except Exception as e:
            logger.error(f"연결 해제 중 예외: {e}")

    def get_serial_object(self) -> serial.Serial:
        return self.ser

    # ─────────────────────────────
    # 내부 통신 헬퍼 (비공개 메서드)
    # ─────────────────────────────
    def _send_cmd(self, payload, pause=0.15):
        if not self.ser or not self.ser.is_open:
            logger.error(f"명령 전송 실패 (연결 없음): {payload}")
            return
            
        frame = f";{payload};".encode("ascii")
        logger.debug(f"[TX] {frame.decode().strip()}")
        self.ser.write(frame)
        self.ser.flush()
        time.sleep(pause)

    def _read_raw(self, max_wait=1.5, idle_gap=0.10):
        if not self.ser or not self.ser.is_open:
            logger.error("읽기 실패 (연결 없음)")
            return b""
        t0 = time.time()
        last = t0
        buf = bytearray()
        while time.time() - t0 < max_wait:
            n = self.ser.in_waiting or 0
            if n > 0:
                chunk = self.ser.read(n)
                if chunk:
                    buf += chunk
                    last = time.time()
            elif len(buf) > 0 and (time.time() - last) >= idle_gap:
                break
            elif n == 0:
                time.sleep(0.01)
        return bytes(buf)

    # ─────────────────────────────
    # 공개 명령: Zeroing
    # ─────────────────────────────
    def zero_position(self):
        """로드셀 값을 0으로 보정합니다. (CDL 명령)"""
        if not self.ser or not self.ser.is_open:
            logger.error("serial 포트가 열려 있지 않습니다.")
            return

        try:
            # 1) 주소 선택 ;S{ADDR};
            self.ser.reset_input_buffer()
            self._send_cmd(f"S21")
            
            # 2) Zeroing ;CDL;
            self._send_cmd("CDL")
            raw_z = self._read_raw()
            asc_z = raw_z.decode("ascii", errors="ignore")
            zcode = _extract_status_code_from_ascii(asc_z)
            if zcode is None:
                logger.warning("[CDL] 상태코드 추출 실패(계속 진행)")
            else:
                logger.info(_interpret_status(zcode, "CDL"))
            
            time.sleep(0.3)
            logger.info("0점 설정 완료")

        except Exception as e:
            logger.error(f"zero_position 예외: {e}")