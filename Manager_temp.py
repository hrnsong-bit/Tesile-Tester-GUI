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
        self.monitor = None
        
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

        # GUI 라벨 업데이트 (1도 단위이므로 그대로 표시)
        for i, val in enumerate(temps, 1):
            if val is not None:
                if hasattr(self.ui, 'temp_channels') and i in self.ui.temp_channels:
                    temp_celsius = val  # 1도 단위이므로 변환 불필요
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
        logger.info("=" * 60)
        logger.info("[apply_settings] 시작")
        
        if not self.controller:
            logger.error("[apply_settings] TempController가 None입니다.")
            
            from PyQt5 import QtWidgets
            QtWidgets.QMessageBox.warning(
                None,
                "연결 오류",
                "온도 제어기가 연결되지 않았습니다.\n먼저 Temp Controller를 연결하세요."
            )
            return
        
        try:
            # 1. UI 위젯 존재 확인
            if not hasattr(self.ui, 'temp_sv_input'):
                logger.error("[apply_settings] temp_sv_input 위젯을 찾을 수 없습니다.")
                return
            
            if not hasattr(self.ui, 'at_exec_combo'):
                logger.error("[apply_settings] at_exec_combo 위젯을 찾을 수 없습니다.")
                return
            
            # 2. CH1 설정 온도 (SV) 읽기
            sv = self.ui.temp_sv_input.value()
            logger.info(f"[apply_settings] UI에서 읽은 SV 값: {sv}°C (type: {type(sv)})")
            
            # 3. 오토튜닝 설정 읽기
            at_index = self.ui.at_exec_combo.currentIndex()
            at_execute = (at_index == 1)  # 0=OFF, 1=ON
            logger.info(f"[apply_settings] UI에서 읽은 AT 설정: index={at_index}, execute={at_execute}")
            
            # 4. Modbus 전송 시작
            logger.info("[apply_settings] Modbus 명령 전송 시작...")
            
            # 4-1. SV 설정
            logger.info(f"[apply_settings] 1/3: CH1 SV 설정 시도 ({sv}°C)")
            result_sv = self.controller.set_sv(1, sv)
            
            # 4-2. 오토튜닝 설정
            logger.info(f"[apply_settings] 2/3: CH1 오토튜닝 설정 시도 ({'ON' if at_execute else 'OFF'})")
            result_at = self.controller.set_at_mode(1, at_execute)
            
            # 4-3. 제어 출력 RUN
            logger.info(f"[apply_settings] 3/3: CH1 제어 출력 RUN 시도")
            result_run = self.controller.set_run_stop(1, run=True)
            
            # 5. 결과 확인
            logger.info("[apply_settings] 결과 확인:")
            logger.info(f"  - SV 설정: {'성공' if result_sv else '실패'}")
            logger.info(f"  - AT 설정: {'성공' if result_at else '실패'}")
            logger.info(f"  - RUN 설정: {'성공' if result_run else '실패'}")
            
            success_count = sum([
                result_sv is not None,
                result_at is not None,
                result_run is not None
            ])
            
            # 6. 사용자 피드백
            from PyQt5 import QtWidgets
            
            if success_count == 3:
                logger.info(f"[apply_settings] ✓ 모든 설정 성공 (3/3)")
                
                QtWidgets.QMessageBox.information(
                    None,
                    "설정 완료",
                    f"CH1 온도 제어 시작\n\n"
                    f"목표 온도: {sv}°C\n"
                    f"오토튜닝: {'실행' if at_execute else '정지'}\n"
                    f"제어 출력: 운전"
                )
            elif success_count > 0:
                logger.warning(f"[apply_settings] ⚠ 부분 성공 ({success_count}/3)")
                
                msg = f"일부 설정만 성공했습니다. ({success_count}/3)\n\n"
                msg += f"SV 설정: {'✓' if result_sv else '✗'}\n"
                msg += f"오토튜닝: {'✓' if result_at else '✗'}\n"
                msg += f"제어 출력: {'✓' if result_run else '✗'}\n\n"
                msg += "실패한 항목은 로그를 확인하세요."
                
                QtWidgets.QMessageBox.warning(None, "설정 부분 실패", msg)
            else:
                logger.error(f"[apply_settings] ✗ 모든 설정 실패 (0/3)")
                
                QtWidgets.QMessageBox.critical(
                    None,
                    "설정 실패",
                    "모든 설정이 실패했습니다.\n\n"
                    "Modbus 통신 상태를 확인하세요.\n"
                    "- 올바른 Slave ID (기본: 1)\n"
                    "- 통신 속도 (기본: 9600)\n"
                    "- 케이블 연결 상태"
                )
                
        except Exception as e:
            logger.error(f"[apply_settings] 예외 발생: {e}", exc_info=True)
            
            from PyQt5 import QtWidgets
            QtWidgets.QMessageBox.critical(
                None,
                "설정 오류",
                f"온도 제어 설정 중 오류 발생:\n{e}"
            )
        
        finally:
            logger.info("=" * 60)