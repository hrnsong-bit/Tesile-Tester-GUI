# Speed_Controller.py
from PyQt5 import QtCore, QtWidgets
from Controller_motor import MotorService # MotorService 타입 힌팅을 위해
import logging

logger = logging.getLogger(__name__)

class SpeedController:
    def __init__(self, ui: 'Ui_MainWindow', lead_mm_per_rev: float):
        self.ui = ui
        self.motor: MotorService | None = None
        
        # === 스크류 사양 ===
        self.lead_mm_per_rev = lead_mm_per_rev
        
        # === 내부 상태 ===
        self.run_speed = 50.0 # 내부 실행 대기 속도 (단위: rps)
        
        logger.info(f"초기화 완료 (Lead: {lead_mm_per_rev} mm/rev)")

    def set_motor(self, motor: MotorService | None):
        self.motor = motor
        if motor:
            logger.info("Motor 객체 주입됨")
            # 연결 시 현재 설정된 속도값을 모터에 즉시 반영
            self.apply_run_speed(also_start=False)
            # Jog 속도도 현재 UI 기준으로 반영
            self._apply_current_jog_speed()
        else:
            logger.info("Motor 객체 해제됨")

    def get_run_speed(self) -> float:
        return self.run_speed

    # ========================
    # 변환 헬퍼 (μm/s → rps)
    # ========================
    def umsec_to_rps(self, um_per_sec: float) -> float:
        """
        μm/s → rps 변환
        """
        mm_per_sec = um_per_sec / 1000.0
        return mm_per_sec / max(self.lead_mm_per_rev, 1e-9)

    # ========================
    # 모드 전환 관련 함수
    # ========================
    def toggle_jog_mode(self, state):
        is_checked = state == QtCore.Qt.Checked
        self.ui.Jog_spinBox.setEnabled(is_checked)
        self.ui.Setjogspeed_pushButton.setEnabled(is_checked)

        self.ui.jog10_radioButton.setEnabled(not is_checked)
        self.ui.jog20_radioButton.setEnabled(not is_checked)
        self.ui.jog30_radioButton.setEnabled(not is_checked)
        self.ui.jog40_radioButton.setEnabled(not is_checked)
        self.ui.jog50_radioButton.setEnabled(not is_checked)
        self.ui.jog100_radioButton.setEnabled(not is_checked)
        self.ui.jog200_radioButton.setEnabled(not is_checked)
        self.ui.jog500_radioButton.setEnabled(not is_checked)

        logger.info(f"[UI] Jog 사용자 모드 {'활성화' if is_checked else '비활성화'}")

    def toggle_jog_speed_mode(self, state):
        is_checked = state == QtCore.Qt.Checked
        self.ui.Setjogspeed_pushButton.setEnabled(is_checked)
        logger.info(f"[UI] 모터 속도 설정 버튼 {'활성화' if is_checked else '비활성화'}")

    def toggle_motor_speed_mode(self, state):
        is_checked = state == QtCore.Qt.Checked

        self.ui.MotorSpeed_spinBox.setEnabled(is_checked)
        self.ui.Setmotorspeed_pushButton.setEnabled(is_checked)

        self.ui.Motor10_radioButton.setEnabled(not is_checked)
        self.ui.Motor20_radioButton.setEnabled(not is_checked)
        self.ui.Motor30_radioButton.setEnabled(not is_checked)
        self.ui.Motor40_radioButton.setEnabled(not is_checked)
        self.ui.Motor50_radioButton.setEnabled(not is_checked)
        self.ui.Motor100_radioButton.setEnabled(not is_checked)
        self.ui.Motor200_radioButton.setEnabled(not is_checked)
        self.ui.Motor300_radioButton.setEnabled(not is_checked)

        logger.info(f"[UI] 지속 회전 속도 {'사용자 정의' if is_checked else '프리셋 선택'} 모드")

    # ========================
    # 속도 설정 함수 (UI: μm/s → 내부: rps)
    # ========================
    
    def _apply_current_jog_speed(self):
        """현재 UI에 선택된 Jog 속도(사용자 지정 또는 라디오)를 모터에 반영합니다."""
        if not self.motor:
            return

        if self.ui.Jog_checkBox.isChecked():
            # 사용자 지정 모드
            speed_um = self.ui.Jog_spinBox.value()
            rps = self.umsec_to_rps(speed_um)
            self.motor.set_jog_speed(rps)
            logger.debug(f"[UI] (적용) Jog 사용자 설정 → {speed_um:.2f} μm/s = {rps:.4f} rps")
        else:
            # 라디오 버튼 모드 (체크된 것 찾기)
            buttons = {
                self.ui.jog10_radioButton: 10,
                # ... (다른 버튼들) ...
                self.ui.jog500_radioButton: 500,
            }
            speed_um = 0
            for btn, val in buttons.items():
                if btn.isChecked():
                    speed_um = val
                    break
            
            if speed_um > 0:
                rps = self.umsec_to_rps(speed_um)
                self.motor.set_jog_speed(rps)
                logger.debug(f"[UI] (적용) Jog 라디오 선택 → {speed_um} μm/s = {rps:.4f} rps")


    def set_jog_speed(self):
        """'Set Speed' (Jog) 버튼 클릭 시 호출"""
        if not self.motor:
            logger.warning("[UI] Jog 속도 설정 실패 (모터 연결 안 됨)")
            return
            
        speed_um = self.ui.Jog_spinBox.value()
        rps = self.umsec_to_rps(speed_um)
        self.motor.set_jog_speed(rps)
        logger.info(f"[UI] Jog 사용자 설정 → {speed_um:.2f} μm/s = {rps:.4f} rps (모터로 {int(rps)} 전송)")

    def set_fixed_jog_speed(self, speed_um, checked):
        """라디오 버튼 (Jog) 클릭 시 호출"""
        if checked and self.motor:
            rps = self.umsec_to_rps(speed_um)
            self.motor.set_jog_speed(rps)
            logger.info(f"[UI] Jog 라디오 선택 → {speed_um} μm/s = {rps:.4f} rps (모터로 {int(rps)} 전송)")

    def apply_run_speed(self, also_start=False):
        """현재 'self.run_speed' 값을 모터에 전송합니다."""
        if not self.motor:
            logger.debug("apply_run_speed 실패 (모터 연결 안 됨)")
            return

        rps = float(self.run_speed)
        logger.debug(f"apply_run_speed() 호출됨, rps={rps:.4f}")
        self.motor.set_continuous_speed(rps)
        logger.debug("set_continuous_speed() 호출 완료")
        if also_start:
            logger.debug("start_speed_mode() 호출 완료 (기능 없음)")

    def set_run_speed(self):
        """'Set Speed' (Motor) 버튼 클릭 시 호출"""
        if self.ui.MotorSpeed_checkBox.isChecked():
            speed_um = self.ui.MotorSpeed_spinBox.value()
            self.run_speed = self.umsec_to_rps(speed_um)
            logger.info(f"[UI] 런 사용자 지정 저장 → {speed_um:.2f} μm/s = {self.run_speed:.4f} rps")
            self.apply_run_speed(also_start=False)

    def set_fixed_run_speed(self, speed_um, checked):
        """라디오 버튼 (Motor) 클릭 시 호출"""
        if checked:
            self.run_speed = self.umsec_to_rps(speed_um)
            logger.info(f"[UI] 런 프리셋 저장 → {speed_um} μm/s = {self.run_speed:.4f} rps")
            self.apply_run_speed(also_start=False)