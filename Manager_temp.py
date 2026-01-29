# Manager_temp.py
from Controller_temp import TempController
from Monitor_temp import TempMonitor
import logging
import time

logger = logging.getLogger(__name__)

class TempManager:
    def __init__(self, ui, plot_service=None):
        self.ui = ui
        self.plot_service = plot_service
        self.controller = None
        self.monitor = None
        self.start_time = None

    def start_service(self, client, interval_ms):
        """연결 성공 시 호출하여 서비스 시작"""
        self.controller = TempController(client)
        self.start_time = time.time()
        
        # 온도 플롯 초기화
        if self.plot_service:
            try:
                self.plot_service.init_temp_plot()
                logger.info("온도 플롯 초기화 완료")
            except Exception as e:
                logger.error(f"온도 플롯 초기화 실패: {e}")
        
        # 모니터 생성
        self.monitor = TempMonitor(client, self.update_all, interval_ms)
        logger.info("Temp Service Started")

    def stop_service(self):
        """연결 해제 시 호출"""
        if self.monitor:
            self.monitor.stop()
        self.controller = None
        
        # 온도 그래프 초기화
        if self.plot_service:
            try:
                self.plot_service.clear_temp_plot()
            except Exception as e:
                logger.error(f"온도 그래프 정리 실패: {e}")
        
        logger.info("Temp Service Stopped")

    def update_all(self, temps: list):
        """모니터링 스레드로부터 데이터를 받아 UI와 그래프 업데이트"""
        elapsed = time.time() - self.start_time

        # GUI 라벨 업데이트
        for i, val in enumerate(temps, 1):
            if val is not None:
                if hasattr(self.ui, 'temp_channels') and i in self.ui.temp_channels:
                    temp_celsius = val
                    self.ui.temp_channels[i]['lbl'].setText(f"{temp_celsius:.1f} °C")

        # 그래프 업데이트
        if self.plot_service:
            try:
                self.plot_service.update_temp_plot(elapsed, temps)
            except Exception as e:
                logger.error(f"온도 그래프 업데이트 실패: {e}")

    def apply_settings(self):
        """
        UI의 설정값을 장비에 전송
        - CH1 SV (설정 온도)
        - 오토 튜닝 실행/정지
        - 제어 출력 운전/정지
        """
        if not self.controller:
            logger.warning("온도 제어기가 연결되지 않았습니다.")
            return
        
        try:
            # 1. CH1 설정 온도 (SV)
            sv = self.ui.temp_sv_input.value()
            result_sv = self.controller.set_sv(1, sv)
            
            # 2. 오토튜닝 설정
            at_index = self.ui.at_exec_combo.currentIndex()
            at_execute = (at_index == 1)  # 0=OFF, 1=ON
            result_at = self.controller.set_at_mode(1, at_execute)
            
            # 3. 제어 출력 운전/정지 (자동으로 RUN 시작)
            # SV를 설정하면 자동으로 제어 시작
            result_run = self.controller.set_run_stop(1, run=True)
            
            # 결과 로깅
            success_count = sum([
                result_sv is not None,
                result_at is not None,
                result_run is not None
            ])
            
            if success_count == 3:
                logger.info(f"[성공] CH1 설정 완료: SV={sv}°C, AT={'ON' if at_execute else 'OFF'}, RUN=ON")
                
                # 사용자에게 알림
                from PyQt5 import QtWidgets
                QtWidgets.QMessageBox.information(
                    None,
                    "설정 완료",
                    f"CH1 온도 제어 시작\n"
                    f"- 목표 온도: {sv}°C\n"
                    f"- 오토튜닝: {'실행' if at_execute else '정지'}\n"
                    f"- 제어 출력: 운전"
                )
            else:
                logger.warning(f"[부분 실패] 3개 중 {success_count}개 성공")
                
        except Exception as e:
            logger.error(f"Settings apply failed: {e}", exc_info=True)
            
            from PyQt5 import QtWidgets
            QtWidgets.QMessageBox.warning(
                None,
                "설정 오류",
                f"온도 제어 설정 중 오류 발생:\n{e}"
            )