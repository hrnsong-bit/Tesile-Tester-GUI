from Controller_temp import TempController
from Monitor_temp import TempMonitor
from Temp_Stabilization import TempStabilizationDetector
from config import temp_cfg, monitor_cfg  # ===== 추가 =====
import logging
import time

logger = logging.getLogger(__name__)


class TempManager:
    def __init__(self, ui, plot_service=None, data_handler=None):
        """
        Args:
            ui: GUI 객체
            plot_service: PlotService 인스턴스
            data_handler: DataHandler 인스턴스
        """
        self.ui = ui
        self.plot_service = plot_service
        self.data_handler = data_handler
        self.controller = None
        self.monitor = None
        self.start_time = None
        self.control_start_time = None
        
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
        self.start_time = time.time()
        
        # 온도 플롯 초기화
        if self.plot_service:
            try:
                if hasattr(self.plot_service, 'init_temp_plot'):
                    self.plot_service.init_temp_plot()
                    logger.info("✓ 온도 플롯 초기화 완료")
            except Exception as e:
                logger.error(f"✗ 온도 플롯 초기화 실패: {e}")
        
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
        
        self.control_active = False
        self.control_start_time = None
        self.stabilization_detector.reset()
        
        if self.plot_service:
            try:
                if hasattr(self.plot_service, 'clear_temp_plot'):
                    self.plot_service.clear_temp_plot()
            except Exception as e:
                logger.error(f"온도 그래프 정리 실패: {e}")
        
        logger.info("Temp Service Stopped")

    def update_all(self, temps: list):
        """모니터링 데이터 업데이트"""
        if self.control_active and self.control_start_time is not None:
            elapsed = time.time() - self.control_start_time
        else:
            elapsed = time.time() - self.start_time

        # GUI 라벨 업데이트
        for i, val in enumerate(temps, 1):
            if val is not None:
                if hasattr(self.ui, 'temp_channels') and i in self.ui.temp_channels:
                    self.ui.temp_channels[i]['lbl'].setText(f"{val:.1f} °C")

        # 제어 활성화 시에만 그래프 업데이트
        if self.control_active:
            if self.plot_service:
                try:
                    if hasattr(self.plot_service, 'update_temp_plot'):
                        self.plot_service.update_temp_plot(elapsed, temps)
                except Exception as e:
                    logger.error(f"온도 그래프 업데이트 실패: {e}")
        
        # DataHandler에 CH1 전달
        if self.data_handler and temps and len(temps) >= 1:
            try:
                self.data_handler.update_temperature_ch1(temps[0])
            except Exception as e:
                logger.error(f"DataHandler 온도 업데이트 실패: {e}")
        
        # 안정화 감지
        if self.control_active and temps and len(temps) >= 1 and temps[0] is not None:
            self.stabilization_detector.check_temperature(temps[0])

    def start_control(self):
        """온도 제어 시작"""
        logger.info("=" * 60)
        logger.info("[start_control] 온도 제어 시작")
        
        if not self.controller:
            logger.error("[start_control] TempController가 None입니다.")
            from PyQt5 import QtWidgets
            QtWidgets.QMessageBox.warning(
                None,
                "연결 오류",
                "온도 제어기가 연결되지 않았습니다."
            )
            return False
        
        try:
            sv = self.ui.temp_sv_input.value()
            at_index = self.ui.at_exec_combo.currentIndex()
            at_execute = (at_index == 1)
            
            logger.info(f"[start_control] 목표: {sv}°C, AT: {at_execute}")
            
            # 그래프 초기화
            if self.plot_service:
                try:
                    if hasattr(self.plot_service, 'clear_temp_plot'):
                        self.plot_service.clear_temp_plot()
                except Exception as e:
                    logger.error(f"그래프 초기화 실패: {e}")
            
            # ===== 수정: 매직 넘버 → config =====
            ch = temp_cfg.DEFAULT_CONTROL_CHANNEL  # ← 1 대신
            
            # Modbus 명령 전송
            result_sv = self.controller.set_sv(ch, sv)
            result_run = self.controller.set_run_stop(ch, run=True)
            result_at = self.controller.set_at_mode(ch, at_execute)
            
            logger.info("[start_control] 결과:")
            logger.info(f"  - SV: {'✓' if result_sv else '✗'}")
            logger.info(f"  - RUN: {'✓' if result_run else '✗'}")
            logger.info(f"  - AT: {'✓' if result_at else '✗'}")
            
            # 안정화 감지 설정
            if hasattr(self.ui, 'temp_stability_enabled'):
                enabled = self.ui.temp_stability_enabled.isChecked()
                tolerance = self.ui.temp_stability_range.value()
                duration_min = self.ui.temp_stability_time.value()
                
                self.stabilization_detector.set_enabled(enabled)
                if enabled:
                    self.stabilization_detector.set_target(sv, tolerance, duration_min)
            
            success_count = sum([
                result_sv is not None,
                result_at is not None,
                result_run is not None
            ])
            
            from PyQt5 import QtWidgets
            
            # ===== 수정: 매직 넘버 → config (판단 기준) =====
            MIN_SUCCESS_COUNT = 2  # 최소 성공 명령 개수
            
            if success_count >= temp_cfg.CONTROL_MIN_SUCCESS_COUNT:
                self.control_start_time = time.time()
                self.control_active = True
                logger.info(f"[start_control] ✓ 제어 시작 완료")
                
                QtWidgets.QMessageBox.information(
                    None,
                    "제어 시작",
                    f"CH{ch} 온도 제어 시작\n\n"
                    f"목표 온도: {sv}°C\n"
                    f"오토튜닝: {'실행' if at_execute else '정지'}"
                )
                return True
            else:
                logger.error("[start_control] ✗ 제어 시작 실패")
                QtWidgets.QMessageBox.critical(
                    None,
                    "제어 실패",
                    "온도 제어 시작 실패"
                )
                return False
                
        except Exception as e:
            logger.error(f"[start_control] 예외: {e}", exc_info=True)
            return False
        
        finally:
            logger.info("=" * 60)
    
    def stop_control(self):
        """온도 제어 정지"""
        logger.info("=" * 60)
        logger.info("[stop_control] 온도 제어 정지")
        
        if not self.controller:
            logger.warning("[stop_control] TempController가 None입니다.")
            return False
        
        try:
            # ===== 수정: 매직 넘버 → config =====
            ch = temp_cfg.DEFAULT_CONTROL_CHANNEL  # ← 1 대신
            
            result = self.controller.set_run_stop(ch, run=False)
            
            if result and not result.isError():
                logger.info("[stop_control] ✓ 제어 정지 성공")
                
                self.control_active = False
                self.control_start_time = None
                self.stabilization_detector.reset()
                
                if self.plot_service:
                    try:
                        if hasattr(self.plot_service, 'clear_temp_plot'):
                            self.plot_service.clear_temp_plot()
                    except Exception as e:
                        logger.error(f"그래프 초기화 실패: {e}")
                
                from PyQt5 import QtWidgets
                QtWidgets.QMessageBox.information(
                    None,
                    "제어 정지",
                    "온도 제어가 정지되었습니다."
                )
                return True
            else:
                logger.warning(f"[stop_control] ✗ 제어 정지 실패")
                return False
                
        except Exception as e:
            logger.error(f"[stop_control] 예외: {e}", exc_info=True)
            return False
        
        finally:
            logger.info("=" * 60)
    
    def _on_stabilization_achieved(self, target: float, tolerance: float, duration_min: float):
        """안정화 완료 시 호출"""
        from PyQt5 import QtWidgets
        
        msg = (
            f"🎯 온도 안정화 완료!\n\n"
            f"목표: {target:.1f}°C ±{tolerance:.1f}°C\n"
            f"유지: {duration_min:.1f}분"
        )
        
        QtWidgets.QMessageBox.information(None, "안정화 완료", msg)
        logger.info(f"[Stabilization] 알림 표시 완료")
