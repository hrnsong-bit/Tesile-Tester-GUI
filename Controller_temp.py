# Controller_temp.py
from pymodbus.client.serial import ModbusSerialClient
import logging

logger = logging.getLogger(__name__)

class TempController:
    def __init__(self, client: ModbusSerialClient):
        self.client = client
        self.slave_id = 1  # TM4 기본 국번

    def set_sv(self, channel: int, value: float):
        """
        CH1~4의 설정 온도(SV)를 변경합니다.
        
        Args:
            channel: 채널 번호 (1~4)
            value: 설정 온도 (°C)
        
        주소:
            TM2: CH1=0x0000, CH2=0x03E8, CH3=0x07D0, CH4=0x0BB8
            TM4: CH1=0x0000 (동일)
        """
        base_addresses = {
            1: 0x0000,  # CH1 SV
            2: 0x03E8,  # CH2 SV
            3: 0x07D0,  # CH3 SV
            4: 0x0BB8   # CH4 SV
        }
        
        addr = base_addresses.get(channel)
        if addr is None:
            logger.error(f"잘못된 채널 번호: {channel}")
            return None
        
        # TM4는 0.1도 단위 (예: 25.0°C → 250)
        val_to_send = int(value * 10)
        
        try:
            result = self.client.write_register(
                address=addr, 
                value=val_to_send, 
                slave=self.slave_id
            )
            
            if result and not result.isError():
                logger.info(f"CH{channel} SV 설정: {value}°C (값: {val_to_send})")
                return result
            else:
                logger.error(f"CH{channel} SV 설정 실패: {result}")
                return None
                
        except Exception as e:
            logger.error(f"CH{channel} SV 설정 예외: {e}")
            return None

    def set_at_mode(self, channel: int, execute: bool):
        """
        오토튜닝 실행/정지
        
        Args:
            channel: 채널 번호 (1~4)
            execute: True=실행(1), False=정지(0)
        
        주소:
            TM2: CH1=0x0064 (100)
            TM4: CH1=0x0064 (100) - 동일
        """
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
        
        try:
            result = self.client.write_register(
                address=addr, 
                value=val, 
                slave=self.slave_id
            )
            
            if result and not result.isError():
                status = "실행" if execute else "정지"
                logger.info(f"CH{channel} 오토튜닝 {status} (주소: 0x{addr:04X}, 값: {val})")
                return result
            else:
                logger.error(f"CH{channel} 오토튜닝 설정 실패: {result}")
                return None
                
        except Exception as e:
            logger.error(f"CH{channel} 오토튜닝 설정 예외: {e}")
            return None

    def set_run_stop(self, channel: int, run: bool):
        """
        제어 출력 운전/정지
        
        Args:
            channel: 채널 번호 (1~4)
            run: True=운전(0), False=정지(1)
        
        주소:
            TM2: CH1=0x0064 (100)
            TM4: CH1=0x0032 (50)  ← 수정됨!
        
        설정:
            0: RUN (운전)
            1: STOP (정지)
        """
        base_addresses = {
            1: 0x0032,  # CH1 RUN/STOP
            2: 0x041A,  # CH2 RUN/STOP (추정)
            3: 0x0802,  # CH3 RUN/STOP (추정)
            4: 0x0BEA   # CH4 RUN/STOP (추정)
        }
        
        addr = base_addresses.get(channel)
        if addr is None:
            logger.error(f"잘못된 채널 번호: {channel}")
            return None
        
        # 주의: 0=RUN, 1=STOP (역논리)
        val = 0 if run else 1
        
        try:
            result = self.client.write_register(
                address=addr, 
                value=val, 
                slave=self.slave_id
            )
            
            if result and not result.isError():
                status = "운전(RUN)" if run else "정지(STOP)"
                logger.info(f"CH{channel} 제어 출력 {status} (주소: 0x{addr:04X}, 값: {val})")
                return result
            else:
                logger.error(f"CH{channel} RUN/STOP 설정 실패: {result}")
                return None
                
        except Exception as e:
            logger.error(f"CH{channel} RUN/STOP 설정 예외: {e}")
            return None

    def read_pv(self, channel: int):
        """
        현재 온도(PV) 읽기
        
        Args:
            channel: 채널 번호 (1~4)
        
        Returns:
            float: 현재 온도 (°C), 실패 시 None
        
        주소:
            CH1=0x03E8 (1000)
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
            result = self.client.read_input_registers(
                address=addr, 
                count=1, 
                slave=self.slave_id
            )
            
            if result and not result.isError() and result.registers:
                raw_val = result.registers[0]
                temp_celsius = raw_val
                return temp_celsius
            else:
                logger.warning(f"CH{channel} PV 읽기 실패: {result}")
                return None
                
        except Exception as e:
            logger.error(f"CH{channel} PV 읽기 예외: {e}")
            return None