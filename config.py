"""
Hardware Configuration
모든 하드웨어 관련 설정값을 집중 관리
"""

from dataclasses import dataclass


@dataclass
class MotorConfig:
    """모터 관련 설정"""
    # 스크류 사양
    LEAD_MM_PER_REV: float = 0.01  # 1회전당 이동거리 (mm)
    
    # 속도 설정
    DEFAULT_SPEED_RPS: float = 50.0  # 기본 속도 (rps)
    MAX_SPEED_RPS: float = 500.0     # 최대 속도 (rps)
    DEFAULT_SAFE_SPEED_RPS: float = 1.0  # ===== 추가: 안전 기본 속도 =====
    
    # Modbus 레지스터 주소
    ADDR_POSITION_HI: int = 0x0075      # 현재 위치 (상위 16bit)
    ADDR_POSITION_LO: int = 0x0076      # 현재 위치 (하위 16bit)
    ADDR_SPEED: int = 0x0132            # 연속 회전 속도
    ADDR_JOG_SPEED: int = 0x0134        # 조깅 속도
    ADDR_TARGET_LO: int = 0x0139        # 목표 위치 (하위)
    ADDR_TARGET_HI: int = 0x013A        # 목표 위치 (상위)
    ADDR_COMMAND: int = 0x0143          # 명령 레지스터
    ADDR_ZERO_POS_LO: int = 0x0141      # 0점 설정 (하위)
    ADDR_ZERO_POS_HI: int = 0x0142      # 0점 설정 (상위)
    
    # Modbus 통신 설정
    DEFAULT_UNIT_ID: int = 1
    DEFAULT_BAUDRATE: int = 9600
    DEFAULT_TIMEOUT: float = 1.0


@dataclass
class LoadcellConfig:
    """로드셀 관련 설정"""
    # 센서 사양
    FULLSCALE: int = 2147483647  # 2^31 - 1 (sint32 max)
    SCALING_FACTOR: float = 100000.0 * -0.0098  # N 단위 변환
    
    # Serial 통신 설정
    DEFAULT_BAUDRATE: int = 9600
    DEFAULT_PARITY: str = 'E'  # Even
    DEFAULT_BYTESIZE: int = 8
    DEFAULT_STOPBITS: int = 1
    DEFAULT_TIMEOUT: float = 1.0
    
    # CDL 명령 주소
    DEVICE_ADDRESS: int = 21  # ;S21;


@dataclass
class TempConfig:
    """온도 제어기 관련 설정"""
    # Modbus 통신 설정
    DEFAULT_BAUDRATE: int = 9600
    DEFAULT_PARITY: str = 'N'  # None
    DEFAULT_UNIT_ID: int = 1
    DEFAULT_TIMEOUT: float = 1.0
    
    # 채널별 Modbus 주소 맵 (TM4 기준)
    CHANNEL_ADDRESSES = {
        1: {
            "PV": 0x03E8,    # 현재 온도 (Process Value)
            "SV": 0x0034,    # 설정 온도 (Set Value)
            "RUN": 0x0032,   # 제어 출력 RUN/STOP
            "AT": 0x0064     # 오토튜닝 실행/정지
        },
        2: {
            "PV": 0x03EE,
            "SV": 0x041C,
            "RUN": 0x041A,
            "AT": 0x044C
        },
        3: {
            "PV": 0x03F4,
            "SV": 0x0804,
            "RUN": 0x0802,
            "AT": 0x0834
        },
        4: {
            "PV": 0x03FA,
            "SV": 0x0BEC,
            "RUN": 0x0BEA,
            "AT": 0x0C1C
        }
    }
    
    # 그래프 색상 (SK 브랜드 컬러)
    CHANNEL_COLORS = [
        '#EA002C',  # SK Red (CH1)
        '#00A0E9',  # SK Blue (CH2)
        '#9BCF0A',  # SK Green (CH3)
        '#F47725'   # SK Orange (CH4)
    ]


@dataclass
class MonitorConfig:
    """모니터링 관련 설정"""
    DEFAULT_INTERVAL_MS: int = 100      # 기본 모니터링 주기 (ms)
    DEFAULT_HZ: int = 10                 # 기본 주파수 (Hz)
    
    # 플롯 설정
    MAX_PLOT_POINTS: int = 10000        # ===== 추가: 최대 플롯 포인트 수 =====
    TEMP_PLOT_WINDOW_SEC: int = 60      # 온도 그래프 표시 범위 (초)


@dataclass
class SafetyConfig:
    """안전 가드 관련 설정"""
    DISPLACEMENT_TOLERANCE_UM: float = 5.0  # 변위 가드 허용 오차 (μm)
    FORCE_TOLERANCE_N: float = 0.1          # 하중 가드 허용 오차 (N)


@dataclass
class PretensionConfig:
    """===== 추가: Pre-Tension 관련 설정 ====="""
    SETTLING_TIME_MS: int = 500  # 진동 안정화 대기 시간 (ms)
    CHECK_INTERVAL_MS: int = 50  # 하중 감시 주기 (ms)


# ===== 전역 접근용 인스턴스 =====
motor_cfg = MotorConfig()
loadcell_cfg = LoadcellConfig()
temp_cfg = TempConfig()
monitor_cfg = MonitorConfig()
safety_cfg = SafetyConfig()
pretension_cfg = PretensionConfig()  # ===== 추가 =====
