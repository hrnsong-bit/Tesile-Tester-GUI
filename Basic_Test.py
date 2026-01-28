# Basic_Test.py
import logging

logger = logging.getLogger(__name__)

class BasicTest:
    def __init__(self, motor, get_run_speed_callback):
        self.motor = motor
        self.get_run_speed = get_run_speed_callback
        self._running = False

    def start(self):
        self._disp_guard_fired = False  
        """당기는 방향(Jog -)으로 연속 이동 시작"""
        if self._running:
            return
        try:
            rps = float(self.get_run_speed())
        except Exception:   
            rps = 1.0  # 안전 기본값

        # 조깅 속도만 맞추고, 바로 Jog- 실행 (당김 전용)
        self.motor.set_jog_speed(rps)
        self.motor.jog_backward()

        logger.info(f"START (pull, Jog-) rps={rps:.3f}")
        self._running = True

    def stop(self):
        """즉시 정지"""
        if not self._running:
            return
        self.motor.stop_motor()
        logger.info("STOP")
        self._running = False