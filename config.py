"""
Hardware Configuration
모든 하드웨어 관련 설정값을 집중 관리
"""

from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MotorConfig:
    """모터 관련 설정"""
    # 스크류 사양
    LEAD_MM_PER_REV: float = 0.01  # 1회전당 이동거리 (mm)
    LEAD_MIN_EPSILON: float = 1e-9  # 리드값 0 방지용 최소값 (분모 보호)
    
    # 속도 설정
    DEFAULT_SPEED_RPS: float = 50.0  # 기본 속도 (rps)
    MAX_SPEED_RPS: float = 500.0     # 최대 속도 (rps)
    DEFAULT_SAFE_SPEED_RPS: float = 1.0  # 안전 기본 속도
    
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
    
    # 레지스터 번호 (10진수)
    REG_POSITION_HI: int = 117  # 0x0075 = 117
    REG_POSITION_LO: int = 118  # 0x0076 = 118
    
    # 데이터 변환 상수
    SINT32_SIGN_BIT: int = 0x80000000      # sint32 부호 비트
    SINT32_OVERFLOW: int = 0x100000000     # sint32 오버플로우 값
    BYTE_MASK_HI: int = 0xFF00             # 상위 바이트 마스크
    BYTE_MASK_LO: int = 0x00FF             # 하위 바이트 마스크
    BYTE_SHIFT: int = 8                    # 바이트 시프트 크기
    
    # 위치 변환 상수
    POSITION_SCALE_FACTOR: float = 10000.0  # 펄스 → mm 변환 계수
    UM_PER_MM: float = 1000.0               # mm → μm 변환
    POSITION_SIGN_INVERT: float = -1.0      # 위치 부호 반전 (하드웨어 특성)
    
    # Modbus 통신 설정
    DEFAULT_UNIT_ID: int = 1
    DEFAULT_BAUDRATE: int = 9600
    DEFAULT_TIMEOUT: float = 1.0


@dataclass
class LoadcellConfig:
    """로드셀 관련 설정"""
    # 센서 사양
    FULLSCALE: int = 2147483647  # 2^31 - 1 (sint32 max)
    SCALING_FACTOR: float = 100000.0 * -0.0098  # N 단위 변환 (통합)
    
    # 데이터 변환 상수
    NORMALIZATION_FACTOR: float = 100000.0  # 정규화 계수
    GRAVITY_FACTOR: float = -0.0098         # 중력 가속도 보정
    
    # Serial 통신 설정
    DEFAULT_BAUDRATE: int = 9600
    DEFAULT_PARITY: str = 'E'  # Even
    DEFAULT_BYTESIZE: int = 8
    DEFAULT_STOPBITS: int = 1
    DEFAULT_TIMEOUT: float = 1.0
    
    # CDL 명령 주소
    DEVICE_ADDRESS: int = 21  # CDL 프로토콜 기본 주소
    
    # 통신 프로토콜 상수
    CMD_SELECT_ADDRESS: str = "S{address}"  # 주소 선택 명령 포맷
    CMD_SINGLE_MEASURE: str = "MSV?"        # 단일 측정 명령
    CMD_ZERO_POSITION: str = "CDL"          # 영점 설정 명령
    FRAME_START: str = ";"                  # 프레임 시작
    FRAME_END: str = ";"                    # 프레임 종료


@dataclass
class TempConfig:
    """온도 제어기 관련 설정"""
    # Modbus 통신 설정
    DEFAULT_BAUDRATE: int = 9600
    DEFAULT_PARITY: str = 'N'  # None
    DEFAULT_UNIT_ID: int = 1
    DEFAULT_TIMEOUT: float = 1.0

    # 제어 시작 최소 성공 명령 수 (SV/RUN/AT 중)
    CONTROL_MIN_SUCCESS_COUNT: int = 2

    # 제어 기본 설정
    DEFAULT_CONTROL_CHANNEL: int = 1        # 기본 제어 채널 (CH1)
    DISCONNECT_DELAY_MS: int = 200          # 연결 해제 시 Modbus 명령 완료 대기 (ms)
    
    # Modbus Handshake 설정
    HANDSHAKE_TEST_ADDRESS: int = 0x0066    # 연결 테스트용 레지스터
    HANDSHAKE_TEST_COUNT: int = 1           # 읽을 레지스터 개수
    
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
    DEFAULT_INTERVAL_MS: int = 100       # 기본 모니터링 주기 (ms)
    DEFAULT_HZ: int = 10                 # 기본 주파수 (Hz)
    
    # 온도 그래프 X축 범위 (초)
    TEMP_PLOT_WINDOW_SEC: int = 60

    # 플롯 설정
    MAX_PLOT_POINTS: int = 10000         # 최대 플롯 포인트 수 (메모리 누수 방지)
    
    # 타이머 설정
    THREAD_WAIT_TIMEOUT_MS: int = 2000   # 스레드 종료 대기 시간 (ms)
    THREAD_SLEEP_BEFORE_QUIT_MS: int = 100  # 스레드 quit 전 대기 (ms)


@dataclass
class SafetyConfig:
    """안전 가드 관련 설정"""
    DISPLACEMENT_TOLERANCE_UM: float = 5.0  # 변위 가드 허용 오차 (μm)
    FORCE_TOLERANCE_N: float = 0.1          # 하중 가드 허용 오차 (N)


@dataclass
class PretensionConfig:
    """Pre-Tension 관련 설정"""
    SETTLING_TIME_MS: int = 500          # 진동 안정화 대기 시간 (ms)
    CHECK_INTERVAL_MS: int = 50          # 하중 감시 주기 (ms)


@dataclass
class SyncConfig:
    """데이터 동기화 설정"""
    MAX_TIME_DIFF_MS: int = 50           # 동기화 허용 오차 (ms)
    BUFFER_SIZE: int = 100               # 동기화 버퍼 크기


@dataclass
class StabilizationConfig:
    """온도 안정화 감지 설정"""
    CHECK_INTERVAL_SEC: float = 1.0      # 온도 체크 주기 (초)
    LOG_INTERVAL_SEC: int = 10           # 진행 상황 로그 주기 (초)


# ===== 전역 접근용 인스턴스 =====
motor_cfg = MotorConfig()
loadcell_cfg = LoadcellConfig()
temp_cfg = TempConfig()
monitor_cfg = MonitorConfig()
safety_cfg = SafetyConfig()
pretension_cfg = PretensionConfig()
sync_cfg = SyncConfig()
stabilization_cfg = StabilizationConfig()


# ===== 설정 검증 함수 =====
def validate_config():
    """설정값 유효성 검증"""
    logger.info("=" * 60)
    logger.info("설정 검증 시작...")
    
    # 1. Motor 설정 검증
    assert motor_cfg.LEAD_MM_PER_REV > 0, \
        f"리드 값은 양수여야 함 (현재: {motor_cfg.LEAD_MM_PER_REV})"
    
    assert 0 < motor_cfg.DEFAULT_SPEED_RPS <= motor_cfg.MAX_SPEED_RPS, \
        f"기본 속도는 0과 최대 속도 사이여야 함"
    
    assert motor_cfg.SINT32_SIGN_BIT == 0x80000000, \
        "SINT32_SIGN_BIT 값이 잘못되었습니다"
    
    assert motor_cfg.POSITION_SCALE_FACTOR > 0, \
        "POSITION_SCALE_FACTOR는 양수여야 함"
    
    logger.info("✓ Motor 설정 검증 완료")
    
    # 2. Loadcell 설정 검증
    assert loadcell_cfg.FULLSCALE > 0, \
        "풀스케일 값은 양수여야 함"
    
    assert 1 <= loadcell_cfg.DEVICE_ADDRESS <= 99, \
        f"장비 주소는 1~99 사이여야 함"
    
    logger.info("✓ Loadcell 설정 검증 완료")
    
    # 3. Temp 설정 검증
    assert len(temp_cfg.CHANNEL_ADDRESSES) == 4, \
        "온도 채널은 4개여야 함"
    
    assert 1 <= temp_cfg.DEFAULT_CONTROL_CHANNEL <= 4, \
        "제어 채널은 1~4 사이여야 함"
    
    assert temp_cfg.DISCONNECT_DELAY_MS > 0, \
        "연결 해제 대기 시간은 양수여야 함"
    
    logger.info("✓ Temp 설정 검증 완료")
    
    # 4. Monitor 설정 검증
    assert monitor_cfg.DEFAULT_INTERVAL_MS > 0, \
        "모니터링 주기는 양수여야 함"
    
    assert monitor_cfg.THREAD_WAIT_TIMEOUT_MS > 0, \
        "스레드 대기 시간은 양수여야 함"
    
    logger.info("✓ Monitor 설정 검증 완료")
    
    # 5. Safety 설정 검증
    assert safety_cfg.DISPLACEMENT_TOLERANCE_UM > 0, \
        "변위 허용 오차는 양수여야 함"
    
    assert safety_cfg.FORCE_TOLERANCE_N > 0, \
        "하중 허용 오차는 양수여야 함"
    
    logger.info("✓ Safety 설정 검증 완료")
    
    # 6. Pretension 설정 검증
    assert pretension_cfg.SETTLING_TIME_MS > 0, \
        "안정화 대기 시간은 양수여야 함"
    
    assert pretension_cfg.CHECK_INTERVAL_MS > 0, \
        "감시 주기는 양수여야 함"
    
    logger.info("✓ Pretension 설정 검증 완료")
    
    # 7. Sync 설정 검증
    assert sync_cfg.MAX_TIME_DIFF_MS > 0, \
        "동기화 허용 오차는 양수여야 함"
    
    assert sync_cfg.BUFFER_SIZE >= 10, \
        f"버퍼 크기는 최소 10 이상 권장"
    
    logger.info("✓ Sync 설정 검증 완료")
    
    # 8. Stabilization 설정 검증
    assert stabilization_cfg.CHECK_INTERVAL_SEC > 0, \
        "온도 체크 주기는 양수여야 함"
    
    assert stabilization_cfg.LOG_INTERVAL_SEC > 0, \
        "로그 주기는 양수여야 함"
    
    logger.info("✓ Stabilization 설정 검증 완료")
    
    logger.info("=" * 60)
    logger.info("✅ 모든 설정 검증 완료")
    logger.info("=" * 60)


# ===== 설정 요약 출력 =====
def print_config_summary():
    """설정값 요약 출력 (디버깅용)"""
    logger.info("=" * 60)
    logger.info("현재 설정값 요약")
    logger.info("=" * 60)
    
    logger.info(f"[Motor]")
    logger.info(f"  - Lead: {motor_cfg.LEAD_MM_PER_REV} mm/rev")
    logger.info(f"  - Max Speed: {motor_cfg.MAX_SPEED_RPS} rps")
    logger.info(f"  - Position Register: {motor_cfg.REG_POSITION_HI}")
    logger.info(f"  - Scale Factor: {motor_cfg.POSITION_SCALE_FACTOR}")
    
    logger.info(f"[Loadcell]")
    logger.info(f"  - Device Address: {loadcell_cfg.DEVICE_ADDRESS}")
    logger.info(f"  - Scaling: {loadcell_cfg.NORMALIZATION_FACTOR} * {loadcell_cfg.GRAVITY_FACTOR}")
    
    logger.info(f"[Temp]")
    logger.info(f"  - Control Channel: {temp_cfg.DEFAULT_CONTROL_CHANNEL}")
    logger.info(f"  - Disconnect Delay: {temp_cfg.DISCONNECT_DELAY_MS} ms")
    
    logger.info(f"[Monitor]")
    logger.info(f"  - Interval: {monitor_cfg.DEFAULT_INTERVAL_MS} ms")
    logger.info(f"  - Thread Timeout: {monitor_cfg.THREAD_WAIT_TIMEOUT_MS} ms")
    
    logger.info(f"[Pretension]")
    logger.info(f"  - Settling Time: {pretension_cfg.SETTLING_TIME_MS} ms")
    logger.info(f"  - Check Interval: {pretension_cfg.CHECK_INTERVAL_MS} ms")
    
    logger.info(f"[Stabilization]")
    logger.info(f"  - Check Interval: {stabilization_cfg.CHECK_INTERVAL_SEC} sec")
    logger.info(f"  - Log Interval: {stabilization_cfg.LOG_INTERVAL_SEC} sec")
    
    logger.info("=" * 60)
