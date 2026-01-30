# Controller_Loadcell.py
import time
import serial
import re
import logging
from config import loadcell_cfg

logger = logging.getLogger(__name__)

_FULLSCALE = loadcell_cfg.FULLSCALE

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
    def __init__(self, ser: serial.Serial = None):
        """
        Args:
            ser: 외부에서 생성된 serial.Serial 객체 (Main.py에서 주입)
        """
        self.ser = ser
        logger.info("LoadcellService 초기화됨 (Serial 객체는 외부 주입)")

    def set_serial(self, ser: serial.Serial):
        """Serial 객체 설정 (Main.py에서 호출)"""
        self.ser = ser
        logger.info(f"Serial 객체 설정됨: {ser.port if ser else None}")

    def get_serial_object(self) -> serial.Serial:
        """Serial 객체 반환"""
        return self.ser

    def _send_cmd(self, payload, pause=0.15):
        if not self.ser or not self.ser.is_open:
            logger.error(f"명령 전송 실패 (연결 없음): {payload}")
            return
            
        frame = f";{payload};".encode("ascii")
        logger.debug(f"[TX] {frame.decode().strip()}")
        self.ser.write(frame)
        self.ser.flush()
        time.sleep(pause)

    def _read_raw(self, max_wait=1.5, idle_gap=0.10) -> bytes:
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

    @staticmethod
    def _to_s32_be(b4: bytes) -> int:
        """빅엔디언 4바이트 → 부호 있는 32비트 정수"""
        if len(b4) != 4:
            raise ValueError(f"4바이트 필요 (받음: {len(b4)})")
        u = (b4[0] << 24) | (b4[1] << 16) | (b4[2] << 8) | b4[3]
        return u - 0x100000000 if (u & 0x80000000) else u

    def zero_position(self):
        """로드셀 값을 0으로 보정 (CDL 명령)"""
        if not self.ser or not self.ser.is_open:
            logger.error("serial 포트가 열려 있지 않습니다.")
            return

        try:
            # 주소 선택
            self.ser.reset_input_buffer()
            self._send_cmd(f"S{loadcell_cfg.DEVICE_ADDRESS}")
            
            # Zeroing
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


# ===== 새로운 함수: Handshake 검증 =====
def verify_loadcell_connection(ser: serial.Serial) -> tuple[bool, str]:
    """
    로드셀 연결 검증 (Handshake)
    
    Args:
        ser: 열린 serial.Serial 객체
        
    Returns:
        (성공 여부, 에러 메시지)
    """
    if not ser or not ser.is_open:
        return (False, "Serial 포트가 열려있지 않음")
    
    try:
        ser.reset_input_buffer()
        time.sleep(0.05)
        
        # 1. 주소 선택 (S21)
        ser.write(f";S{loadcell_cfg.DEVICE_ADDRESS};".encode("ascii"))
        ser.flush()
        time.sleep(0.15)
        
        # 응답 읽기
        t0 = time.time()
        last = t0
        buf = bytearray()
        while time.time() - t0 < 1.0:
            n = ser.in_waiting or 0
            if n > 0:
                chunk = ser.read(n)
                if chunk:
                    buf += chunk
                    last = time.time()
            elif len(buf) > 0 and (time.time() - last) >= 0.1:
                break
            elif n == 0:
                time.sleep(0.01)
        
        raw_s = bytes(buf)
        logger.debug(f"[Handshake] S21 응답: {_hex_dump(raw_s)}")
        
        if len(raw_s) < 2:
            err = f"주소 선택 응답 없음 (길이: {len(raw_s)})"
            logger.error(f"[Handshake] {err}")
            return (False, err)
        
        # 2. 단일 측정 명령 (MSV?)
        ser.reset_input_buffer()
        ser.write(b";MSV?;")
        ser.flush()
        
        t0 = time.time()
        last = t0
        buf = bytearray()
        while time.time() - t0 < 1.5:
            n = ser.in_waiting or 0
            if n > 0:
                chunk = ser.read(n)
                if chunk:
                    buf += chunk
                    last = time.time()
            elif len(buf) > 0 and (time.time() - last) >= 0.1:
                break
            elif n == 0:
                time.sleep(0.01)
        
        raw_msv = bytes(buf)
        logger.debug(f"[Handshake] MSV? 응답: {_hex_dump(raw_msv)}")
        
        if len(raw_msv) < 4:
            err = f"측정 명령 응답 없음 (길이: {len(raw_msv)})"
            logger.error(f"[Handshake] {err}")
            return (False, err)
        
        # 3. 응답 검증 (첫 4바이트가 숫자 데이터인지 확인)
        first4 = raw_msv[:4]
        try:
            u = (first4[0] << 24) | (first4[1] << 16) | (first4[2] << 8) | first4[3]
            counts = u - 0x100000000 if (u & 0x80000000) else u
            logger.info(f"[Handshake] 성공 - 측정값: {counts} counts")
            return (True, "")
        
        except Exception as e:
            err = f"응답 파싱 실패: {e}"
            logger.error(f"[Handshake] {err}")
            return (False, err)

    except Exception as e:
        err = f"예상치 못한 오류: {e}"
        logger.error(f"[Handshake] {err}", exc_info=True)
        return (False, err)
