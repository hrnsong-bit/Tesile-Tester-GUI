# Controller_motor.py
from pymodbus.client.serial import ModbusSerialClient
import time
import serial
import logging

logger = logging.getLogger(__name__)

class MotorService:
    def __init__(self, client: ModbusSerialClient, unit_id=1):
        """
        ModbusSerialClient 객체를 외부에서 주입받습니다.
        """
        self.client = client
        self.unit_id = unit_id 

    # ─────────────────────────────
    # 헬퍼: 32-bit 조합
    # ─────────────────────────────
    @staticmethod
    def _u32_from_hi_lo(hi, lo):
        return ((hi & 0xFFFF) << 16) | (lo & 0xFFFF)

    @staticmethod
    def _s32(x):
        return x - 0x100000000 if (x & 0x80000000) else x

    @staticmethod
    def _byte(val16, which):  # which: 'hi' or 'lo'
        return (val16 >> 8) & 0xFF if which == 'hi' else (val16 & 0xFF)

    # ─────────────────────────────
    # 현재 위치 읽기
    # ─────────────────────────────
    def _read_current_position_debug(self):
        if not self.client or not self.client.is_socket_open():
             logger.debug("read_current_position: 연결 없음")
             return None
        try:
            rr = self.client.read_holding_registers(address=0x0075, count=2)
            logger.debug(f"curpos read object: {rr}")
            regs = getattr(rr, "registers", None)
            logger.debug(f"curpos registers: {regs}")

            if rr.isError() or not regs or len(regs) != 2:
                logger.warning("curpos read 실패")
                return None
            
            hi, lo = regs[0], regs[1]
            u32_std = self._u32_from_hi_lo(hi, lo)
            s32_std = self._s32(u32_std)
            r126, r127 = regs[0], regs[1]

            r126_hi = (r126 >> 8) & 0xFF
            r126_lo =  r126       & 0xFF
            r127_hi = (r127 >> 8) & 0xFF
            r127_lo =  r127       & 0xFF

            u32_mon = ((r127_hi << 24) | (r127_lo << 16) | (r126_hi << 8) | r126_lo)
            s32_mon = self._s32(u32_mon)

            return {"std": s32_std, "mon": s32_mon}
        except Exception as e:
            logger.error(f"curpos read 예외: {e}")
            return None

    # ─────────────────────────────
    # 기본 명령: send/조그/정지/속도 설정/읽기들
    # ─────────────────────────────
    def send_command(self, address, value):
        if not self.client or not self.client.is_socket_open():
             logger.error(f"명령 전송 실패: (연결 없음) address={hex(address)}")
             return None
        try:
            return self.client.write_register(address=address, value=value)
        except Exception as e:
            logger.error(f"명령 전송 실패 (address={hex(address)}): {e}")

    def jog_forward(self):
        logger.info("[모터] 전진 명령")
        return self.send_command(0x0143, 4)  # JOG Forward

    def jog_backward(self):
        logger.info("[모터] 후진 명령")
        return self.send_command(0x0143, 5)  # JOG Backward

    def stop_motor(self):
        logger.info("[모터] 정지 명령")
        return self.send_command(0x0143, 6)  # Stop

    def set_jog_speed(self, speed_rps):
        try:
            # 1 RPS 단위로 보정 (0.01 rps 단위 아님)
            value = int(speed_rps) 
            logger.info(f"조깅 속도 설정 → {speed_rps} rps (전송 값: {value})")
            # 조그 속도 레지스터 (0x0134)
            result = self.send_command(0x0134, value)
            if result is not None and not result.isError():
                logger.debug("속도 설정 성공")
            else:
                logger.error("속도 설정 실패 (통신 오류 또는 응답 없음)")
        except Exception as e:
            logger.error(f"속도 설정 중 예외 발생: {e}")

    def set_continuous_speed(self, speed_rps):
        try:
            # 1 RPS 단위 보정 (set_jog_speed와 동일)
            value = int(speed_rps)
            logger.info(f"지속 회전(절대이동) 속도 설정 → {speed_rps} rps (전송 값: {value})")
            
            # 주소: 0x0132 (매뉴얼 Step 1 확인)
            result = self.send_command(0x0132, value) 
            if result is not None and not result.isError():
                logger.debug("지속 속도 설정 성공")
            else:
                logger.error("지속 속도 설정 실패 (통신 오류 또는 응답 없음)")
        except Exception as e:
            logger.error(f"지속 속도 설정 중 예외 발생: {e}")

    def read_holding_register(self, address):
        if not self.client or not self.client.is_socket_open():
            logger.warning(f"레지스터 {hex(address)} 읽기 실패 (연결 없음)")
            return 0
        try:
            result = self.client.read_holding_registers(address=address, count=1)
            if result.isError() or not result.registers:
                logger.warning(f"레지스터 {hex(address)} 읽기 실패")
                return 0
            return result.registers[0]
        except Exception as e:
            logger.error(f"레지스터 {hex(address)} 읽기 중 예외 발생: {e}")
            return 0

    def read_target_position(self):
        if not self.client or not self.client.is_socket_open():
            logger.warning("위치 읽기 실패 (연결 없음)")
            return 0
        try:
            result = self.client.read_holding_registers(address=0x0139, count=2)
            if result.isError() or not result.registers or len(result.registers) < 2:
                logger.warning("Target 위치 읽기 실패")
                return 0
            
            lo, hi = result.registers
            u32_val = (hi << 16) | lo
            position = self._s32(u32_val) 
            
            logger.debug(f"Target 위치: {position} (Lo={lo}, Hi={hi})")
            return position
        except Exception as e:
            logger.error(f"위치 읽기 예외: {e}")
            return 0
            
    # ─────────────────────────────
    # zero_position: 정지→0,0 쓰기(0x0141)→커맨드8(0x0143)
    # ─────────────────────────────
    def zero_position(self) -> bool:
        # (이 기능은 "현재 위치를 0점으로 설정"하는 기능(커맨드 8)으로,
        # "0점 위치로 이동"하는 move_to_absolute(커맨드 1)와는 다름)
        if not self.client or not self.client.is_socket_open():
            logger.error("0점 설정 실패 (연결 없음)")
            return False
        try:
            self.stop_motor() 
            time.sleep(0.05)

            w = self.client.write_registers(address=0x0141, values=[0x0000, 0x0000])
            if (not w) or (hasattr(w, "isError") and w.isError()):
                logger.error(f"0값 쓰기 실패: {w}")
                return False

            c = self.client.write_register(address=0x0143, value=8)
            if (not c) or (hasattr(c, "isError") and c.isError()):
                logger.error(f"커맨드8 트리거 실패: {c}")
                return False

            time.sleep(0.05)
            logger.info("0점 설정 시퀀스 완료: 정지→값쓰기(0x1B)→커맨드8 OK")
            return True
        except Exception as e:
            logger.error(f"0점 설정 예외: {e}")
            return False

    # ─────────────────────────────
    # ========== 핵심 기능: 3단계 수행 ==========
    # ─────────────────────────────
    def move_to_absolute(self, target_pulses, speed_rps):
        """[매뉴얼 기반 수정] 지정한 절대 위치(pulses)로 이동합니다."""
        if not self.client or not self.client.is_socket_open():
            logger.error("절대 이동 실패 (연결 없음)")
            return False

        try:
            # 1. 이동 속도 설정 (Step 1: 0x0132)
            self.set_continuous_speed(speed_rps) 
            
            # 2. 32-bit 펄스 값을 16-bit 레지스터 2개로 분리
            s32_pulses = int(target_pulses)
            u32_pulses = s32_pulses & 0xFFFFFFFF 
            
            hi = (u32_pulses >> 16) & 0xFFFF
            lo = u32_pulses & 0xFFFF
            
            # 3. 목표 위치 레지스터 (Step 2: 0x0139)에 쓰기
            # Lo/Hi 순서로 전송 (매뉴얼 -5000 예제 기준)
            w = self.client.write_registers(address=0x0139, values=[lo, hi]) 
            if (not w) or (hasattr(w, "isError") and w.isError()):
                logger.error(f"목표 위치(0x0139)[{s32_pulses} pulses -> Lo={lo}, Hi={hi}] 쓰기 실패: {w}")
                return False

            # 4. 절대 위치 이동 트리거 (Step 3: 0x0143에 '1')
            logger.info(f"[모터] 절대 이동 명령(1) -> {s32_pulses} pulses (Speed: {speed_rps} rps)")
            c = self.send_command(0x0143, 1) # <--- 1 = Absolute running (매뉴얼 확인)
            if (not c) or (hasattr(c, "isError") and c.isError()):
                logger.error(f"절대 이동 트리거(1) 실패: {c}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"move_to_absolute 예외: {e}")
            return False