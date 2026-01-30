import logging
import time
from PyQt5 import QtCore
from config import pretension_cfg  # ===== 추가 =====

logger = logging.getLogger(__name__)


class PretensionTest(QtCore.QObject):
    """Pre-Tension Test"""
    
    finished = QtCore.pyqtSignal() 

    def __init__(self, motor_service, loadcell_service, data_handler):
        super().__init__()
        self.motor = motor_service
        self.lc_service = loadcell_service
        self.data = data_handler
        
        self._running = False
        self._target_load = 0.0
        
        # ===== 수정: 매직 넘버 → config =====
        self.timer = QtCore.QTimer()
        self.timer.setInterval(pretension_cfg.CHECK_INTERVAL_MS)  # ← 50 대신
        self.timer.timeout.connect(self._check_load_loop)
        
        logger.info("PretensionTest 초기화 완료")

    def start(self, target_speed_rps: float, target_load_n: float):
        """
        Pre-Tension 시작
        
        Args:
            target_speed_rps: 이동 속도 (rps)
            target_load_n: 목표 하중 (N, 절대값)
        """
        if self._running:
            logger.warning("[PreTension] 이미 실행 중입니다.")
            return
        
        self._target_load = abs(target_load_n)
        self._running = True
        
        logger.info(f"[PreTension] 시작 - 속도: {target_speed_rps:.2f} rps, 목표: {self._target_load:.3f} N")
        
        try:
            # 모터 속도 설정 및 이동 시작
            self.motor.set_jog_speed(target_speed_rps)
            self.motor.jog_backward()  # 당기는 방향
            
            # 타이머 시작 (하중 감시)
            self.timer.start()
            
            logger.info("[PreTension] 이동 시작, 하중 감시 활성화")
        
        except Exception as e:
            logger.error(f"[PreTension] 시작 실패: {e}", exc_info=True)
            self._running = False

    def stop(self):
        """Pre-Tension 정지"""
        if not self._running:
            return
        
        self._running = False
        self.timer.stop()
        
        try:
            self.motor.stop_motor()
            logger.info("[PreTension] 모터 정지 완료")
        except Exception as e:
            logger.error(f"[PreTension] 정지 실패: {e}")

    def _check_load_loop(self):
        """타이머 콜백 - 하중 체크"""
        if not self._running:
            return

        current_force = abs(self.data.last_force)
        
        if current_force >= self._target_load:
            logger.info(
                f"[PreTension] 목표 하중 도달! "
                f"(현재: {current_force:.3f} N >= 목표: {self._target_load} N)"
            )
            
            # 1. 즉시 정지
            self.stop()
            
            # ===== 수정: 매직 넘버 → config =====
            # 2. 진동 안정화 대기 후 0점 설정
            QtCore.QTimer.singleShot(
                pretension_cfg.SETTLING_TIME_MS,  # ← 500 대신
                self._perform_zeroing
            )

    def _perform_zeroing(self):
        """진동 안정화 후 자동 0점 설정"""
        logger.info("[PreTension] 자동 0점 설정 시작...")
        zeroing_success = True

        # 1. 로드셀 0점
        try:
            self.lc_service.zero_position()
            logger.info("[PreTension] 로드셀 0점 완료")
        except Exception as e:
            logger.error(f"[PreTension] 로드셀 0점 실패: {e}")
            zeroing_success = False

        # 2. 모터 0점
        try:
            self.motor.zero_position()
            logger.info("[PreTension] 모터 엔코더 0점 완료")
        except Exception as e:
            logger.error(f"[PreTension] 모터 0점 실패: {e}")
            zeroing_success = False

        if zeroing_success:
            logger.info("[PreTension] ✓ 모든 과정 완료")
        else:
            logger.warning("[PreTension] ✗ 일부 과정 실패")
        
        # Main.py에 완료 신호
        self.finished.emit()
