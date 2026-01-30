# Manager_temp.py

from Controller_temp import TempController
from Monitor_temp import TempMonitor
from Temp_Stabilization import TempStabilizationDetector
from config import temp_cfg, monitor_cfg
import logging
import time

logger = logging.getLogger(__name__)


class TempManager:
    def __init__(self, ui, plot_service=None, data_handler=None):
        """
        Args:
            ui: GUI 객체
            plot_service: PlotService 인스턴스
            data_handler: DataHandler 인스턴스 (Test 로그용)
        """
        self.ui = ui
        self.plot_service = plot_service
        self.data_handler = data_handler
        self.controller = None
        self.monitor = None
        self.start_time = None
        self.control_start_time = None
        
        # ===== 추가: 제어 시작 시간 =====
        self.control_start_time = None  # 제어 시작 시점의 timestamp
        
        # 제어 상태 플래그
        self.control_active = False
        
        # 안정화 감지기
        self.stabilization_detector = TempStabilizationDetector()
        self.stabilization_detector.stabilization_achieved.connect(
            self._on_stabilization_achieved
        )
        
        logger.info("TempManager 초기화 완료")

    def start_service(self, client, interval_ms=None):
        """연결 성공 시 호출하여 서비스 시작"""
        if interval_ms is None:
            interval_ms = monitor_cfg.DEFAULT_INTERVAL_MS
            
        self.controller = TempController(client)
        self.start_time = time.time()  # 모니터링 시작 시간 (연결 시점)
        
        # 온도 플롯 명시적 초기화 (빈 상태로)
        if self.plot_service:
            try:
                if hasattr(self.plot_service, 'init_temp_plot'):
                    self.plot_service.init_temp_plot()
                    logger.info("✓ 온도 플롯 초기화 완료 (Manager에서 호출)")
                else:
                    logger.warning("PlotService에 init_temp_plot 메서드가 없습니다.")
            except Exception as e:
                logger.error(f"✗ 온도 플롯 초기화 실패: {e}")
        else:
            logger.warning("PlotService가 None이므로 온도 플롯을 초기화하지 않습니다.")
        
        # 모니터 생성
        self.monitor = TempMonitor(client, self.update_all, interval_ms)
        logger.info(f"Temp Service Started (Interval: {interval_ms}ms)")
        
        return True

    def stop_service(self):
        """연결 해제 시 호출"""
        if self.monitor:
            self.monitor.stop()
        self.controller = None
        self.monitor = None
        
        # 제어 상태 플래그 리셋
        self.control_active = False
        self.control_start_time = None
        
        # 안정화 감지 리셋
        self.stabilization_detector.reset()
        
        # 온도 그래프 초기화
        if self.plot_service:
            try:
                if hasattr(self.plot_service, 'clear_temp_plot'):
                    self.plot_service.clear_temp_plot()
            except Exception as e:
                logger.error(f"온도 그래프 정리 실패: {e}")
        
        logger.info("Temp Service Stopped")

    def update_all(self, temps: list):
        """
        모니터링 스레드로부터 데이터를 받아 UI와 그래프 업데이트
        """
        # ===== 수정: 제어 활성화 시에는 제어 시작 시점부터의 경과 시간 사용 =====
        if self.control_active and self.control_start_time is not None:
            elapsed = time.time() - self.control_start_time  # 제어 시작부터의 시간
        else:
            elapsed = time.time() - self.start_time  # 연결 시점부터의 시간 (사용 안 함)

        # GUI 라벨 업데이트 (4채널 모두 - 항상 표시)
        for i, val in enumerate(temps, 1):
            if val is not None:
                if hasattr(self.ui, 'temp_channels') and i in self.ui.temp_channels:
                    temp_celsius = val
                    self.ui.temp_channels[i]['lbl'].setText(f"{temp_celsius:.1f} °C")

        # 제어가 활성화된 경우에만 그래프 업데이트
        if self.control_active:
            if self.plot_service:
                try:
                    if hasattr(self.plot_service, 'update_temp_plot'):
                        # ===== 수정: 제어 시작 시점부터의 시간 전달 =====
                        self.plot_service.update_temp_plot(elapsed, temps)
                except Exception as e:
                    logger.error(f"온도 그래프 업데이트 실패: {e}", exc_info=True)
        
        # DataHandler에 CH1만 전달 (Test 로그용 - 항상 전달)
        if self.data_handler and temps and len(temps) >= 1:
            try:
                self.data_handler.update_temperature_ch1(temps[0])
            except Exception as e:
                logger.error(f"DataHandler 온도 업데이트 실패: {e}")
        
        # 안정화 감지 (CH1만, 제어 활성화 시에만)
        if self.control_active and temps and len(temps) >= 1 and temps[0] is not None:
            self.stabilization_detector.check_temperature(temps[0])

    def start_control(self):
        """
        온도 제어 시작 (Start 버튼 클릭 시 호출)
        """
        logger.info("=" * 60)
        logger.info("[start_control] 온도 제어 시작")
        
        if not self.controller:
            logger.error("[start_control] TempController가 None입니다.")
            
            from PyQt5 import QtWidgets
            QtWidgets.QMessageBox.warning(
                None,
                "연결 오류",
                "온도 제어기가 연결되지 않았습니다.\n먼저 Temp Controller를 연결하세요."
            )
            return False
        
        try:
            if not hasattr(self.ui, 'temp_sv_input'):
                logger.error("[start_control] temp_sv_input 위젯을 찾을 수 없습니다.")
                return False
            
            if not hasattr(self.ui, 'at_exec_combo'):
                logger.error("[start_control] at_exec_combo 위젯을 찾을 수 없습니다.")
                return False
            
            sv = self.ui.temp_sv_input.value()
            logger.info(f"[start_control] 목표 온도: {sv}°C")
            
            at_index = self.ui.at_exec_combo.currentIndex()
            at_execute = (at_index == 1)
            logger.info(f"[start_control] 오토튜닝: {'ON' if at_execute else 'OFF'}")
            
            # ===== 그래프 초기화 후 시작 =====
            if self.plot_service:
                try:
                    if hasattr(self.plot_service, 'clear_temp_plot'):
                        self.plot_service.clear_temp_plot()
                        logger.info("[start_control] 그래프 초기화 완료")
                except Exception as e:
                    logger.error(f"[start_control] 그래프 초기화 실패: {e}")
            
            # Modbus 명령 전송
            logger.info("[start_control] Modbus 명령 전송 시작...")
            
            # 1. SV 설정
            result_sv = self.controller.set_sv(1, sv)
            
            # 2. 제어 출력 RUN
            result_run = self.controller.set_run_stop(1, run=True)
            
            # 3. 오토튜닝 설정
            result_at = self.controller.set_at_mode(1, at_execute)
            
            logger.info("[start_control] 결과:")
            logger.info(f"  - SV: {'✓' if result_sv else '✗'}")
            logger.info(f"  - RUN: {'✓' if result_run else '✗'}")
            logger.info(f"  - AT: {'✓' if result_at else '✗'}")
            
            # 안정화 감지 설정
            if hasattr(self.ui, 'temp_stability_enabled') and \
               hasattr(self.ui, 'temp_stability_range') and \
               hasattr(self.ui, 'temp_stability_time'):
                
                enabled = self.ui.temp_stability_enabled.isChecked()
                tolerance = self.ui.temp_stability_range.value()
                duration_min = self.ui.temp_stability_time.value()
                
                self.stabilization_detector.set_enabled(enabled)
                if enabled:
                    self.stabilization_detector.set_target(sv, tolerance, duration_min)
                    logger.info(
                        f"[start_control] 안정화 감지: "
                        f"{sv}°C ±{tolerance}°C, {duration_min}분"
                    )
            
            success_count = sum([
                result_sv is not None,
                result_at is not None,
                result_run is not None
            ])
            
            from PyQt5 import QtWidgets
            
            if success_count >= 2:  # 최소 2개 성공
                # ===== 제어 시작 시간 기록 (0초 시작점) =====
                self.control_start_time = time.time()
                self.control_active = True
                logger.info(f"[start_control] ✓ 제어 시작 완료 - 시간 초기화 (t=0초)")
                
                QtWidgets.QMessageBox.information(
                    None,
                    "제어 시작",
                    f"CH1 온도 제어 시작\n\n"
                    f"목표 온도: {sv}°C\n"
                    f"오토튜닝: {'실행' if at_execute else '정지'}\n"
                    f"제어 출력: 운전\n\n"
                    f"그래프 시간이 0초로 초기화되었습니다."
                )
                return True
            else:
                logger.error("[start_control] ✗ 제어 시작 실패")
                
                QtWidgets.QMessageBox.critical(
                    None,
                    "제어 실패",
                    "온도 제어 시작에 실패했습니다.\n\n"
                    "Modbus 통신 상태를 확인하세요."
                )
                return False
                
        except Exception as e:
            logger.error(f"[start_control] 예외: {e}", exc_info=True)
            
            from PyQt5 import QtWidgets
            QtWidgets.QMessageBox.critical(
                None,
                "설정 오류",
                f"온도 제어 시작 중 오류 발생:\n{e}"
            )
            return False
        
        finally:
            logger.info("=" * 60)
    
    def stop_control(self):
        """
        온도 제어 정지 (Stop 버튼 클릭 시 호출)
        제어만 정지하고 그래프는 초기화
        """
        logger.info("=" * 60)
        logger.info("[stop_control] 온도 제어 정지")
        
        if not self.controller:
            logger.warning("[stop_control] TempController가 None입니다.")
            return False
        
        try:
            # CH1 제어 출력 정지
            result = self.controller.set_run_stop(1, run=False)
            
            if result and not result.isError():
                logger.info("[stop_control] ✓ 제어 정지 성공")
                
                # ===== 제어 비활성화, 시간 초기화, 그래프 초기화 =====
                self.control_active = False
                self.control_start_time = None  # ===== 추가: 시간 초기화 =====
                self.stabilization_detector.reset()
                
                if self.plot_service:
                    try:
                        if hasattr(self.plot_service, 'clear_temp_plot'):
                            self.plot_service.clear_temp_plot()
                            logger.info("[stop_control] 그래프 및 시간 초기화 완료")
                    except Exception as e:
                        logger.error(f"[stop_control] 그래프 초기화 실패: {e}")
                
                from PyQt5 import QtWidgets
                QtWidgets.QMessageBox.information(
                    None,
                    "제어 정지",
                    "온도 제어가 정지되었습니다.\n"
                    "그래프와 시간이 초기화되었습니다."
                )
                return True
            else:
                logger.warning(f"[stop_control] ✗ 제어 정지 실패: {result}")
                return False
                
        except Exception as e:
            logger.error(f"[stop_control] 예외: {e}", exc_info=True)
            return False
        
        finally:
            logger.info("=" * 60)
    
    def _on_stabilization_achieved(self, target: float, tolerance: float, duration_min: float):
        """
        안정화 완료 시 호출
        제어는 유지, 알림만 표시
        """
        from PyQt5 import QtWidgets
        
        msg = (
            f"🎯 온도 안정화 완료!\n\n"
            f"목표 온도: {target:.1f}°C\n"
            f"허용 범위: ±{tolerance:.1f}°C\n"
            f"유지 시간: {duration_min:.1f}분\n\n"
            f"설정한 조건이 충족되었습니다.\n"
            f"제어는 계속 유지됩니다."
        )
        
        QtWidgets.QMessageBox.information(
            None,
            "안정화 완료",
            msg
        )
        
        logger.info(f"[Stabilization] 알림 표시 완료 (제어는 계속 유지)")
