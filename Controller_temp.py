# Controller_temp.py
from pymodbus.client.serial import ModbusSerialClient
import logging

logger = logging.getLogger(__name__)

class TempController:
    def __init__(self, client: ModbusSerialClient):
        self.client = client

    def set_sv(self, channel: int, value: float):
        """
        CH1~4의 설정 온도(SV)를 변경합니다.
        """
        logger.info(f"[set_sv] 호출됨 - channel={channel}, value={value}°C (type={type(value)})")
        
        base_addresses = {
            1: 0x0034,  # CH1 SV
            2: 0x041C,  # CH2 SV
            3: 0x0804,  # CH3 SV
            4: 0x0BEC   # CH4 SV
        }
        
        addr = base_addresses.get(channel)
        if addr is None:
            logger.error(f"잘못된 채널 번호: {channel}")
            return None
        
        val_to_send = int(value)
        
        logger.info(f"[set_sv] 전송 준비 - addr=0x{addr:04X}, val_to_send={val_to_send}")
        
        try:
            if not self.client or not self.client.is_socket_open():
                logger.error("[set_sv] Modbus 클라이언트가 연결되지 않았습니다.")
                return None
            
            result = self.client.write_register(
                address=addr, 
                value=val_to_send,
                device_id=1
            )
            
            logger.info(f"[set_sv] Modbus 응답: {result}")
            
            if result and not result.isError():
                logger.info(f"✓ CH{channel} SV 설정 성공: {value}°C (전송값: {val_to_send})")
                return result
            else:
                logger.error(f"✗ CH{channel} SV 설정 실패: {result}")
                return None
                
        except Exception as e:
            logger.error(f"✗ CH{channel} SV 설정 예외: {e}", exc_info=True)
            return None

    def set_at_mode(self, channel: int, execute: bool):
        """
        오토튜닝 실행/정지
        """
        logger.info(f"[set_at_mode] 호출됨 - channel={channel}, execute={execute}")
        
        base_addresses = {
            1: 0x0064,  # CH1 Auto-Tuning
            2: 0x044C,  # CH2 Auto-Tuning
            3: 0x0834,  # CH3 Auto-Tuning
            4: 0x0C1C   # CH4 Auto-Tuning
        }
        
        addr = base_addresses.get(channel)
        if addr is None:
            logger.error(f"잘못된 채널 번호: {channel}")
            return None
        
        val = 1 if execute else 0
        
        logger.info(f"[set_at_mode] 전송 준비 - addr=0x{addr:04X}, val={val}")
        
        try:
            if not self.client or not self.client.is_socket_open():
                logger.error("[set_at_mode] Modbus 클라이언트가 연결되지 않았습니다.")
                return None
            
            result = self.client.write_register(
                address=addr, 
                value=val,
                device_id=1
            )
            
            logger.info(f"[set_at_mode] Modbus 응답: {result}")
            
            if result and not result.isError():
                status = "실행" if execute else "정지"
                logger.info(f"✓ CH{channel} 오토튜닝 {status} 성공")
                return result
            else:
                logger.error(f"✗ CH{channel} 오토튜닝 설정 실패: {result}")
                return None
                
        except Exception as e:
            logger.error(f"✗ CH{channel} 오토튜닝 설정 예외: {e}", exc_info=True)
            return None

    def set_run_stop(self, channel: int, run: bool):
        """
        제어 출력 운전/정지
        """
        logger.info(f"[set_run_stop] 호출됨 - channel={channel}, run={run}")
        
        base_addresses = {
            1: 0x0032,  # CH1 RUN/STOP
            2: 0x041A,  # CH2 RUN/STOP
            3: 0x0802,  # CH3 RUN/STOP
            4: 0x0BEA   # CH4 RUN/STOP
        }
        
        addr = base_addresses.get(channel)
        if addr is None:
            logger.error(f"잘못된 채널 번호: {channel}")
            return None
        
        val = 0 if run else 1
        
        logger.info(f"[set_run_stop] 전송 준비 - addr=0x{addr:04X}, val={val}")
        
        try:
            if not self.client or not self.client.is_socket_open():
                logger.error("[set_run_stop] Modbus 클라이언트가 연결되지 않았습니다.")
                return None
            
            result = self.client.write_register(
                address=addr, 
                value=val,
                device_id=1
            )
            
            logger.info(f"[set_run_stop] Modbus 응답: {result}")
            
            if result and not result.isError():
                status = "운전(RUN)" if run else "정지(STOP)"
                logger.info(f"✓ CH{channel} 제어 출력 {status} 성공")
                return result
            else:
                logger.error(f"✗ CH{channel} RUN/STOP 설정 실패: {result}")
                return None
                
        except Exception as e:
            logger.error(f"✗ CH{channel} RUN/STOP 설정 예외: {e}", exc_info=True)
            return None

    def read_pv(self, channel: int):
        """
        현재 온도(PV) 읽기
        """
        base_addresses = {
            1: 0x03E8,  # CH1 PV
            2: 0x03EE,  # CH2 PV
            3: 0x03F4,  # CH3 PV
            4: 0x03FA   # CH4 PV
        }
        
        addr = base_addresses.get(channel)
        if addr is None:
            logger.error(f"잘못된 채널 번호: {channel}")
            return None
        
        try:
            if not self.client or not self.client.is_socket_open():
                return None
            
            result = self.client.read_input_registers(
                address=addr, 
                count=1,
                device_id=1
            )
            
            if result and not result.isError() and result.registers:
                raw_val = result.registers[0]
                return raw_val
            else:
                logger.debug(f"CH{channel} PV 읽기 실패")
                return None
                
        except Exception as e:
            logger.error(f"CH{channel} PV 읽기 예외: {e}")
            return None
