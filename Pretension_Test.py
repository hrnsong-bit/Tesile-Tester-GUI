# Pretension_Test.py
import logging
import time
from PyQt5 import QtCore

logger = logging.getLogger(__name__)

class PretensionTest(QtCore.QObject):
    # 모든 과정(이동 -> 정지 -> 0점)이 끝나면 Main에 알려주는 신호
    finished = QtCore.pyqtSignal() 

    def __init__(self, motor_service, loadcell_service, data_handler):
        super().__init__()
        self.motor = motor_service
        self.lc_service = loadcell_service
        self.data = data_handler
        
        self._running = False
        self._target_load = 0.0
        
        # 0.05초(50ms)마다 하중을 감시하는 타이머
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50) 
        self.timer.timeout.connect(self._check_load_loop)

    def start(self, target_speed_rps, target_load_n):
        """
        [Pre-Tension 시퀀스 시작]
        1. 목표 하중의 부호 확인 -> 모터 방향 결정 (양수: 당기기 / 음수: 밀기)
        2. 모터 속도 설정 (속도는 절대값 사용)
        3. 모터 이동 시작
        4. 하중 감시 시작
        """
        if self._running:
            logger.warning("[PreTension] 이미 실행 중입니다.")
            return

        # 1. 방향 결정 로직
        # 하중이 양수(+)면 당기기(Backward), 음수(-)면 밀기(Forward)
        is_pulling = (target_load_n >= 0)
        direction_str = "당기기(Backward, Tension)" if is_pulling else "밀기(Forward, Compression)"

        # 2. 목표치 설정 (감시는 절대값으로 함)
        self._target_load = abs(target_load_n)
        abs_speed = abs(target_speed_rps) # 속도도 절대값으로

        logger.info(f"[PreTension] 시작: {direction_str}, 속도={abs_speed:.2f} rps, 목표하중(절대값)={self._target_load} N")

        # 3. 모터 속도 입력
        try:
            self.motor.set_jog_speed(abs_speed) 
        except Exception as e:
            logger.error(f"[PreTension] 속도 설정 실패: {e}")
            return

        # 4. 모터 이동 명령 (방향에 따라 분기)
        try:
            if is_pulling:
                self.motor.jog_backward() # 당기기
            else:
                self.motor.jog_forward()  # 밀기
        except Exception as e:
            logger.error(f"[PreTension] 이동 명령 실패: {e}")
            return
        
        # 5. 감시 타이머 시작
        self._running = True
        self.timer.start()

    def stop(self):
        """강제 정지 또는 목표 도달 시 호출"""
        if not self._running:
            return
            
        self.timer.stop()       # 감시 중단
        self.motor.stop_motor() # 모터 정지
        self._running = False
        logger.info("[PreTension] 정지됨.")

    def _check_load_loop(self):
        """타이머에 의해 계속 호출되면서 하중을 체크하는 함수"""
        if not self._running:
            return

        # 현재 하중의 '크기(절대값)'를 가져옴
        current_force = abs(self.data.last_force)
        
        # [핵심 로직] 현재 힘이 목표 힘보다 커지면 정지
        if current_force >= self._target_load:
            logger.info(f"[PreTension] 목표 하중 감지! (현재: {current_force:.3f} N >= 목표: {self._target_load} N)")
            
            # 1. 즉시 정지
            self.stop()
            
            # 2. 기계적 진동이 멈출 때까지 0.5초 대기 후 -> 0점 잡기 실행
            QtCore.QTimer.singleShot(500, self._perform_zeroing)

    def _perform_zeroing(self):
        """멈춘 뒤 자동으로 0점을 잡는 함수"""
        logger.info("[PreTension] 자동 0점 설정(Zeroing) 시작...")
        zeroing_success = True

        # 1. 로드셀 0점
        try:
            self.lc_service.zero_position()
            logger.info("[PreTension] 로드셀 0점 완료")
        except Exception as e:
            logger.error(f"[PreTension] 로드셀 0점 실패: {e}")
            zeroing_success = False

        # 2. 모터 0점 (현재 위치를 0으로 인식)
        try:
            self.motor.zero_position()
            logger.info("[PreTension] 모터 엔코더 0점 완료")
        except Exception as e:
            logger.error(f"[PreTension] 모터 0점 실패: {e}")
            zeroing_success = False

        if zeroing_success:
            logger.info("[PreTension] 모든 과정 완료")
        else:
            logger.warning("[PreTension] 일부 과정 실패")
        
        # Main.py에 완료 신호 보냄 (메시지창 표시용)
        self.finished.emit()