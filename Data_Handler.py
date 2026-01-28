# Data_Handler.py
from PyQt5 import QtWidgets
from Plot_Service import PlotService # PlotService 타입 힌팅
from typing import Callable # 콜백 함수 타입 힌팅
import logging

logger = logging.getLogger(__name__)

class DataHandler:
    def __init__(self, ui: 'Ui_MainWindow', plot_service: PlotService | None, stop_all_tests_callback: Callable):

        self.ui = ui
        self.plot_service = plot_service
        self.stop_all_tests_callback = stop_all_tests_callback # 중앙 정지 함수

        # === 가드 로직용 상태 변수 ===
        self.start_pos_um = 0.0
        self.last_force = 0.0
        self.last_pos_um = 0.0
        
        self._disp_guard_fired = False
        self._force_guard_fired = False

        # ========== 텐셔닝 상태 변수 추가 ==========

        self.is_tensioning = False
        self.tension_threshold = 0.0
        # ==========================================
        
        logger.info("초기화 완료")

    # ========================
    # 가드 제어 메서드 (Main.py에서 호출)
    # ========================
    def reset_disp_guard(self):
        self._disp_guard_fired = False

    def reset_force_guard(self):
        self._force_guard_fired = False
        
    def reset_all_guards(self):
        self.reset_disp_guard()
        self.reset_force_guard()
        logger.info("모든 가드 리셋됨")

    #  ========== 텐셔닝 제어 메서드==========
    def start_tensioning(self, threshold_N: float):
        """텐셔닝 모드를 시작합니다. (양수/음수 모두 허용)"""
        #  0 이하(<=)가 아닌, 0일 때만 거부하도록 수정
        if threshold_N == 0.0:
            logger.error(f"텐셔닝 감지 하중은 0이 될 수 없습니다: {threshold_N}")
            return
            
        self.is_tensioning = True
        self.tension_threshold = threshold_N
        # 메인 가드 플래그는 리셋
        self.reset_all_guards()
        logger.info(f"텐셔닝 모드 시작. 목표 하중: {threshold_N:.3f} N")

    def stop_tensioning(self):
        """텐셔닝 모드를 수동으로 중지합니다."""
        self.is_tensioning = False
        logger.info("텐셔닝 모드 중지.")
    # ============================================

    def capture_start_position(self):
        """테스트 시작 시점의 위치를 캡처합니다."""
        self.start_pos_um = self.last_pos_um
        logger.info(f"시작 위치 캡처: {self.start_pos_um:.1f} um")

    def reset_ui_labels(self):
        """연결 해제 시 관련 UI 라벨을 초기화합니다."""
        logger.info("UI 라벨 초기화")
        # Setting 탭
        if hasattr(self.ui, "En0Positionnow_label"):
            self.ui.En0Positionnow_label.setText("")
        if hasattr(self.ui, "Load0Currentnow_label"):
            self.ui.Load0Currentnow_label.setText("")
        
        # Test 탭
        if hasattr(self.ui, "test_pos_label"):
            self.ui.test_pos_label.setText("0.0")
        if hasattr(self.ui, "test_load_label"):
            self.ui.test_load_label.setText("0.000")

    # ========================
    # 엔코더 업데이트 콜백
    # ========================
    def update_motor_position(self, pos_um, *_):
        try:
            # 1) 표시 갱신
            current_pos_um = float(pos_um)
            if hasattr(self, "ui") and hasattr(self.ui, "En0Positionnow_label"):
                self.ui.En0Positionnow_label.setText(f"{current_pos_um:.1f} [um]")

            if hasattr(self, "ui") and hasattr(self.ui, "test_pos_label"):
                self.ui.test_pos_label.setText(f"{current_pos_um:.1f} [um]")

            # 2) 최신 위치 저장
            self.last_pos_um = current_pos_um 
            
            # 텐셔닝 모드일 때는 변위 가드 비활성화
            if self.is_tensioning:
                return
            
            # 3) 한계(mm) 읽기 → μm로 변환
            limit_mm = 0.0
            try:
                if hasattr(self, "ui") and hasattr(self.ui, "DisplaceLimitMax_doubleSpinBox"):
                    limit_mm = float(self.ui.DisplaceLimitMax_doubleSpinBox.value())
            except Exception:
                limit_mm = 0.0

            if limit_mm <= 0:
                self._disp_guard_fired = False
                return

            limit_um = limit_mm * 1000.0
            tol_um = getattr(self, "disp_tol_um", 5.0)

            # 4) '총' 변위 변화량 계산
            pos_delta = abs(self.last_pos_um - self.start_pos_um)

            # 5) '총' 변위 변화량 가드
            if (not self._disp_guard_fired) and (pos_delta >= (limit_um - tol_um)):
                logger.warning(f"[GUARD] ΔPos(Total)={pos_delta:.1f} (start={self.start_pos_um:.1f}, now={self.last_pos_um:.1f}) ≥ limit={limit_um:.1f} (tol={tol_um} μm) → STOP")
                
                self.stop_all_tests_callback(reason=f"변위 가드 발동 (ΔPos={pos_delta:.1f})")
                self._disp_guard_fired = True

        except Exception as e:
            logger.error(f"update_motor_position 예외: {e}")

    # ========================
    # 로드셀 업데이트 콜백
    # ========================
    def update_loadcell_value(self, norm_x100k: float, *_):
        try:
            # 1) 현재 값(new)과 이전 값(old)을 명확히 구분
            current_force = float(norm_x100k)
            previous_force = self.last_force

            # 2) 표시 갱신 (현재 값으로)
            if hasattr(self, "ui") and hasattr(self.ui, "Load0Currentnow_label"):
               self.ui.Load0Currentnow_label.setText(f"{current_force:.3f} [N]") 

            if hasattr(self, "ui") and hasattr(self.ui, "test_load_label"):
               self.ui.test_load_label.setText(f"{current_force:.3f} [N]")

            #  ========== 텐셔닝 로직 ==========
            if self.is_tensioning:
                
                stop_condition_met = False
                
                # 1. 목표 하중이 양수일 때 (인장, 당기기)
                if self.tension_threshold > 0:
                    if current_force >= self.tension_threshold:
                        stop_condition_met = True
                
                # 2. 목표 하중이 음수일 때 (압축, 밀기)
                elif self.tension_threshold < 0:
                    if current_force <= self.tension_threshold:
                        stop_condition_met = True
                
                # 3. 정지 조건 충족 시
                if stop_condition_met:
                    logger.warning(f"[TENSION] 목표 하중 도달 (Target: {self.tension_threshold:.3f} N, Current: {current_force:.3f} N) -> STOP")
                    self.is_tensioning = False # 플래그를 먼저 내림
                    self.stop_all_tests_callback(reason="텐셔닝 하중 도달")
                
                # 텐셔닝 중에는 플로팅/가드 로직을 건너뛰고 값만 갱신
                self.last_force = current_force
                return # Early exit
            # ==============================================

            # ========== PlotService에 데이터 전송 ==========
            if self.plot_service:
                       self.plot_service.update_data(current_force, self.last_pos_um)

            # 3) 한계 읽기
            limit_val = 0.0
            try:
                if hasattr(self, "ui") and hasattr(self.ui, "ForceLimitMax_doubleSpinBox"):
                    limit_val = float(self.ui.ForceLimitMax_doubleSpinBox.value())
                elif hasattr(self, "ui") and hasattr(self.ui, "LoadcellLimitMax_doubleSpinBox"):
                    limit_val = float(self.ui.LoadcellLimitMax_doubleSpinBox.value())
            except Exception:
                limit_val = 0.0

            if limit_val <= 0:
                self._force_guard_fired = False
            else:
                # 4) '주기당' 변화율 계산
                force_delta = abs(current_force - previous_force)
                
                # 5) 변화율 가드
                if (not getattr(self, "_force_guard_fired", False)) and (force_delta >= limit_val):
                    logger.warning(f"[GUARD:LC] ΔF/cycle={force_delta:.3f} (prev={previous_force:.3f}, now={current_force:.3f}) ≥ limit={limit_val:.3f} N/cycle → STOP")
                    
                    self.stop_all_tests_callback(reason=f"하중 가드 발동 (ΔF={force_delta:.3f})")
                    self._force_guard_fired = True

            # 6) 중요: 모든 로직이 끝난 후, '이전 값'을 '현재 값'으로 업데이트
            self.last_force = current_force

        except Exception as e:
            logger.error(f"update_loadcell_value 예외: {e}")