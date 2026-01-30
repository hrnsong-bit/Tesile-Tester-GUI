# Main.py
import time
import serial
import pymodbus
import sys
import logging
import Logging_Config

# 로깅 설정 실행
Logging_Config.setup_logging()

# Main.py 자신의 로거 가져오기
logger = logging.getLogger(__name__)

logger.info(f"실행 중인 Python 경로: {sys.executable}")
logger.info(f"실행 중인 Python 버전: {sys.version}")
logger.info(f"pymodbus 버전: {pymodbus.__version__}")


logger.info(f"Using pymodbus version: {pymodbus.__version__}")

from serial.tools import list_ports
from PyQt5 import QtWidgets, QtCore, QtGui
from GUI import Ui_MainWindow
from Controller_motor import MotorService
from Controller_Loadcell import LoadcellService
from pymodbus.client.serial import ModbusSerialClient

# ===== 리팩토링된 모듈 임포트 =====
from Data_Synchronizer import DataSynchronizer
from Safety_Guard import SafetyGuard
from Tensioning_Controller import TensioningController
from UI_Updater import UIUpdater
from Data_Handler import DataHandler
from Plot_Service import PlotService

from Manager_motor import MotorManager
from Manager_loadcell import LoadcellManager
from Manager_temp import TempManager

from Basic_Test import BasicTest
from Ui_Binding import bind_main_signals
from Speed_Controller import SpeedController

# ===== 새로 추가된 모듈 =====
from ErrorHandler import ErrorHandler
from Settings_Manager import SettingsManager

# ===== config.py 임포트 =====
from config import motor_cfg, loadcell_cfg, temp_cfg, monitor_cfg, safety_cfg

try:
    from Pretension_Test import PretensionTest
except ImportError:
    PretensionTest = None
    logger.warning("Pretension_Test.py를 찾을 수 없어 Pretension 기능을 사용할 수 없습니다.")


class MainWindow(QtWidgets.QMainWindow):

    # ========================
    # UI 생성 및 슬롯 (Hz 설정)
    # ========================
    
    def _on_set_hz(self):
        """'Set Frequency' 버튼 클릭 시 호출될 슬롯"""
        try:
            hz_val = self.ui.hz_spinBox.value() 
            if hz_val <= 0:
                ErrorHandler.show_warning("입력 오류", "Frequency는 0보다 커야 합니다.", self)
                return
            
            # Hz를 ms로 변환하여 저장
            self.monitor_interval_ms = int(1000 / hz_val)
            logger.info(f"[HZ] Monitor interval set to {self.monitor_interval_ms} ms ({hz_val} Hz)")

            # ===== 설정 저장 =====
            self.settings_mgr.save_monitoring_hz(hz_val)

            # Manager를 통해 간접 업데이트
            if self.motor_manager.is_monitoring():
                self.motor_manager.monitor.update_interval(self.monitor_interval_ms)
                logger.info("[HZ] Motor monitor interval updated.")
            
            if self.loadcell_manager.is_monitoring():
                self.loadcell_manager.monitor.update_interval(self.monitor_interval_ms)
                logger.info("[HZ] Loadcell monitor interval updated.")

            ErrorHandler.show_success(
                "Frequency Set", 
                f"모니터링 주파수가 {hz_val} Hz ({self.monitor_interval_ms} ms)로 설정되었습니다.",
                self
            )

        except Exception as e:
            logger.error(f"[HZ] Error setting frequency: {e}")
            ErrorHandler.show_error("오류", f"주파수 설정 중 오류 발생: {e}", self)
            
    # ========================
    # 컨트롤러 슬롯
    # ========================

    def on_lc_set_clicked(self):
        try:
            if not self.loadcell_manager.is_connected():
                ErrorHandler.show_not_connected_error("Loadcell", self)
                return

            logger.info(f"[INFO] CDL Zeroing 요청...")
            self.loadcell_manager.zero_calibration()
        
        except Exception as e:
            logger.error(f"[ERR] Zeroing 실패: {e}")
            ErrorHandler.show_error("영점 설정 오류", f"Zeroing 실패: {e}", self)

    def on_zero_encoder_clicked(self):
        if self.motor_manager.is_connected():
            self.motor_manager.controller.zero_position()
        else:
            ErrorHandler.show_not_connected_error("Motor", self)

    def on_reset_clicked(self):
        """Reset 버튼 클릭 시: 가드 리셋 + 모터 원점 복귀"""
        logger.info("[Reset] 버튼 클릭됨")

        # DataHandler를 통해 가드 리셋
        self.data_handler.reset_guards()
        
        if self.motor_manager.is_connected():
            safe_speed_rps = 10 
            target_pos = 0
            
            logger.info(f"[Reset] 가드 리셋 완료. 모터를 원점({target_pos})으로 이동합니다.")
            
            success = self.motor_manager.controller.move_to_absolute(target_pos, safe_speed_rps)
            
            if success:
                ErrorHandler.show_success("Reset", "모터가 원점(0)으로 이동합니다.", self)
            else:
                ErrorHandler.show_warning("Reset", "모터 이동 명령 실패 (통신 오류)", self)
        else:
            ErrorHandler.show_warning("Reset", "모터가 연결되지 않아 이동은 생략합니다.", self)

    def on_pretension_start(self):
        if not self.pretension_test or not self.motor_manager.is_connected():
            ErrorHandler.show_warning(
                "오류", 
                "모터가 연결되지 않았거나 Pretension 기능이 준비되지 않았습니다.",
                self
            )
            return

        speed_val_um = self.ui.tension_speed_spinBox.value()
        target_load_n = self.ui.tension_force_spinBox.value()
        
        rps_speed = speed_val_um / 10.0 
        
        self.pretension_test.start(target_speed_rps=rps_speed, target_load_n=target_load_n)

    def on_pretension_stop(self):
        if self.pretension_test:
            self.pretension_test.stop()

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ===== SettingsManager 초기화 =====
        self.settings_mgr = SettingsManager()

        # ===== 1. 의존성 없는 컴포넌트부터 생성 =====
        
        # PlotService (IDataReceiver 구현체)
        try:
            self.plot_service = PlotService(
                self, 
                self.ui.graphicsView,
                ui=self.ui,
                temp_plot_widget=self.ui.temp_plot
            )
        except Exception as e:
            logger.error(f"PlotService 초기화 실패: {e}")
            self.plot_service = None

        # UI Updater
        self.ui_updater = UIUpdater(self.ui)
        
        # Safety Guard
        self.safety_guard = SafetyGuard(self.ui, safety_cfg)
        
        # Data Synchronizer
        self.data_synchronizer = DataSynchronizer(buffer_size=100)
        
        # Tensioning Controller
        self.tensioning = TensioningController()
        
        # ===== 2. DataHandler 생성 (모든 의존성 주입) =====
        self.data_handler = DataHandler(
            ui_updater=self.ui_updater,
            safety_guard=self.safety_guard,
            synchronizer=self.data_synchronizer,
            tensioning=self.tensioning,
            data_receiver=self.plot_service,
            stop_callback=self._stop_all_tests
        ) 
        
        # ===== 3. Manager 생성 =====
        self.motor_manager = MotorManager(data_handler=self.data_handler)
        self.loadcell_manager = LoadcellManager(data_handler=self.data_handler)
        self.temp_manager = TempManager(
            self.ui, 
            plot_service=self.plot_service,
            data_handler=self.data_handler
        )
        
        # ===== 온도 버튼 연결 =====
        if hasattr(self.ui, 'temp_start_btn') and hasattr(self.ui, 'temp_stop_btn'):
            try:
                self.ui.temp_start_btn.clicked.disconnect()
                self.ui.temp_stop_btn.clicked.disconnect()
            except:
                pass
            self.ui.temp_start_btn.clicked.connect(self.on_temp_start)
            self.ui.temp_stop_btn.clicked.connect(self.on_temp_stop)
            logger.info("✓ 온도 Start/Stop 버튼 연결 완료")
        else:
            logger.error("✗ temp_start_btn 또는 temp_stop_btn 위젯을 찾을 수 없습니다.")

        # ===== Data 탭 서브 탭 삽입 =====
        try:
            from Data_Repack import TabDICUTM, TabMultiCompare, TabPreprocessor
            
            if self.ui.data_tab_layout.count() > 0:
                item = self.ui.data_tab_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                    logger.debug("Data 탭의 placeholder 라벨 제거 완료")
        except Exception as e:
            logger.warning(f"Data 탭 placeholder 제거 실패: {e}")

        try:
            self.ss_curve_widget = TabDICUTM()
            self.preprocessor_widget = TabPreprocessor()
            self.multi_compare_widget = TabMultiCompare()

            self.data_sub_tabs = QtWidgets.QTabWidget()
            
            self.data_sub_tabs.addTab(self.ss_curve_widget, "SS Curve Generator")
            self.data_sub_tabs.addTab(self.preprocessor_widget, "CSV Preprocessor")
            self.data_sub_tabs.addTab(self.multi_compare_widget, "Multi Compare") 

            self.ui.data_tab_layout.addWidget(self.data_sub_tabs)
            
            logger.info("Data 탭에 SS Curve Gen, CSV Preprocessor, Multi Compare 서브 탭 삽입 완료")
        except Exception as e:
            logger.error(f"Data 탭 서브 탭 생성 실패: {e}")

        # ===== 모니터링 주파수 설정 =====
        # ===== 저장된 Hz 값 불러오기 =====
        saved_hz = self.settings_mgr.load_monitoring_hz()
        self.monitor_interval_ms = int(1000 / saved_hz)
        self.ui.hz_spinBox.setValue(saved_hz)
        logger.info(f"저장된 모니터링 주파수 복원: {saved_hz} Hz")
        
        if hasattr(self.ui, 'hz_set_pushButton'):
            self.ui.hz_set_pushButton.clicked.connect(self._on_set_hz)

        # ===== 버튼 연결 =====
        self.ui.Load0_pushButton.clicked.connect(self.on_lc_set_clicked)

        # ===== Modbus 클라이언트 (Manager가 관리) =====
        self.motor_client = None
        self.temp_client = None
        
        # ===== 하위 호환성 속성 (Deprecated) =====
        self.motor = None
        self.loadcell_service = None
        self.motor_monitor = None
        self.lc_monitor = None

        # ===== Speed Controller =====
        self.speed_controller = SpeedController(
            ui=self.ui, 
            lead_mm_per_rev=motor_cfg.LEAD_MM_PER_REV
        )
        logger.info("SpeedController 초기화 완료")

        # ===== Pretension Test =====
        self.pretension_test = None

        # ===== SpinBox 접미사 제거 =====
        try:
            self.ui.Jog_spinBox.setSuffix("")
            self.ui.MotorSpeed_spinBox.setSuffix("")
        except Exception:
            pass

        # ===== COM 포트 UI 초기화 =====
        self._init_com_ui()

        # ===== 버튼 초기 상태 설정 =====
        self.ui.Setjogspeed_pushButton.setEnabled(False)
        self.ui.Jog_spinBox.setEnabled(False)
        self.ui.MotorSpeed_spinBox.setEnabled(False)
        self.ui.Setmotorspeed_pushButton.setEnabled(False)
        
        # ===== Basic Test 초기화 =====
        self.basic_test = None

        # ===== UI 시그널 바인딩 =====
        bind_main_signals(self.ui, self)
        logger.info("초기화 및 시그널 바인딩 완료")

        # ===== Basic Test 버튼 연결 =====
        start_btn = getattr(self.ui, "Basicteststart_pushButton", None)
        if start_btn:
            try:
                start_btn.clicked.disconnect()
            except Exception:
                pass
            start_btn.clicked.connect(self.on_basic_test_start)

        stop_btn = getattr(self.ui, "Basicteststop_pushButton", None)
        if stop_btn:
            try:
                stop_btn.clicked.disconnect()
            except Exception:
                pass
            stop_btn.clicked.connect(self.on_basic_test_stop)

        reset_btn = getattr(self.ui, "Basictestreset_pushButton", None)
        if reset_btn:
            try:
                reset_btn.clicked.disconnect()
            except Exception:
                pass
            reset_btn.clicked.connect(self.on_reset_clicked)

        # ===== Pretension 버튼 연결 =====
        if hasattr(self.ui, "tension_start_pushButton"):
            self.ui.tension_start_pushButton.clicked.connect(self.on_pretension_start)
        if hasattr(self.ui, "tension_stop_pushButton"):
            self.ui.tension_stop_pushButton.clicked.connect(self.on_pretension_stop)

        # ===== 초기 버튼 정책 강제 적용 =====
        self._force_initial_button_policy()
        QtCore.QTimer.singleShot(0, self._force_initial_button_policy)

        # ===== 윈도우 위치/크기 복원 =====
        self._restore_window_geometry()

        # ===== 저장된 안전 제한값 복원 =====
        self._restore_safety_limits()

    def closeEvent(self, event):
        """프로그램 종료 시 설정 저장 및 모든 서비스 정리"""
        try:
            # ===== 1. 온도 제어 정지 (하드웨어) =====
            logger.info("[CLOSE] 프로그램 종료 - 온도 제어 정지 시작")
            self._stop_temp_control_safely()
        
            # ===== 2. 약간의 대기 (Modbus 명령 완료) =====
            QtCore.QThread.msleep(200)
        
            # ===== 3. 모든 Manager 서비스 중지 (스레드 종료) =====
            logger.info("[CLOSE] 모든 서비스 중지 시작")
        
            if hasattr(self, 'temp_manager') and self.temp_manager:
                try:
                   self.temp_manager.stop_service()  # ← 추가!
                   logger.info("[CLOSE] ✓ TempManager 서비스 중지 완료")
                except Exception as e:
                    logger.error(f"[CLOSE] TempManager 중지 실패: {e}")
        
            if hasattr(self, 'motor_manager') and self.motor_manager:
                try:
                    self.motor_manager.stop_service()
                    logger.info("[CLOSE] ✓ MotorManager 서비스 중지 완료")
                except Exception as e:
                    logger.error(f"[CLOSE] MotorManager 중지 실패: {e}")
        
            if hasattr(self, 'loadcell_manager') and self.loadcell_manager:
                try:
                    self.loadcell_manager.stop_service()
                    logger.info("[CLOSE] ✓ LoadcellManager 서비스 중지 완료")
                except Exception as e:
                    logger.error(f"[CLOSE] LoadcellManager 중지 실패: {e}")
        
            # ===== 4. Modbus 클라이언트 종료 =====
            if hasattr(self, 'temp_client') and self.temp_client:
                try:
                    self.temp_client.close()
                    logger.info("[CLOSE] ✓ Temp Modbus 클라이언트 종료 완료")
                except Exception as e:
                    logger.error(f"[CLOSE] Temp 클라이언트 종료 실패: {e}")
        
            if hasattr(self, 'motor_client') and self.motor_client:
                try:
                    self.motor_client.close()
                    logger.info("[CLOSE] ✓ Motor Modbus 클라이언트 종료 완료")
                except Exception as e:
                    logger.error(f"[CLOSE] Motor 클라이언트 종료 실패: {e}")
        
            # ===== 5. 설정 저장 =====
            try:
                self.settings_mgr.save_window_geometry(self.saveGeometry())
                self.settings_mgr.save_window_state(self.saveState())
            
                self.settings_mgr.save_displacement_limit(
                    self.ui.DisplaceLimitMax_doubleSpinBox.value()
                )
                self.settings_mgr.save_force_limit(
                    self.ui.ForceLimitMax_doubleSpinBox.value()
                )
            
                self.settings_mgr.sync()
                logger.info("[CLOSE] ✓ 설정 저장 완료")
            except Exception as e:
                logger.error(f"[CLOSE] 설정 저장 실패: {e}")
        
            # ===== 6. 스레드 종료 대기 =====
            QtCore.QThread.msleep(300)
        
            logger.info("[CLOSE] ==================== 프로그램 종료 완료 ====================")
        
        except Exception as e:
            logger.error(f"[CLOSE] closeEvent 예외: {e}", exc_info=True)
    
            event.accept()

    def _stop_temp_control_safely(self):
        """
        온도 제어를 안전하게 정지하는 내부 메서드
        여러 곳에서 호출 가능
        """
        if not hasattr(self, 'temp_manager') or not self.temp_manager:
            logger.debug("[TEMP_STOP] TempManager 없음 (정지 건너뜀)")
            return
            
        if not self.temp_manager.controller:
            logger.debug("[TEMP_STOP] TempController 없음 (정지 건너뜀)")
            return
        
        try:
            logger.info("[TEMP_STOP] 온도 제어 정지 시도 (RUN/STOP → STOP)")
            
            # CH1 제어 출력 정지
            result = self.temp_manager.controller.set_run_stop(1, run=False)
            
            if result and not result.isError():
                logger.info("[TEMP_STOP] ✓ 온도 제어 정지 성공")
                
                # 제어 플래그, 시간, 그래프 초기화
                self.temp_manager.control_active = False
                self.temp_manager.control_start_time = None  # ===== 추가 =====
                self.temp_manager.stabilization_detector.reset()
                
                if self.temp_manager.plot_service:
                    try:
                        if hasattr(self.temp_manager.plot_service, 'clear_temp_plot'):
                            self.temp_manager.plot_service.clear_temp_plot()
                            logger.info("[TEMP_STOP] 그래프 및 시간 초기화 완료")
                    except Exception as e:
                        logger.error(f"[TEMP_STOP] 그래프 초기화 실패: {e}")
            else:
                logger.warning(f"[TEMP_STOP] ✗ 온도 제어 정지 실패: {result}")

        except Exception as e:
            logger.error(f"[TEMP_STOP] 온도 제어 정지 중 예외: {e}", exc_info=True)


    def _restore_window_geometry(self):
        """저장된 윈도우 위치/크기 복원"""
        try:
            geometry = self.settings_mgr.load_window_geometry()
            if geometry:
                self.restoreGeometry(geometry)
                logger.info("윈도우 위치/크기 복원 완료")
            
            state = self.settings_mgr.load_window_state()
            if state:
                self.restoreState(state)
                logger.info("윈도우 상태 복원 완료")
        except Exception as e:
            logger.error(f"윈도우 설정 복원 실패: {e}")

    def _restore_safety_limits(self):
        """저장된 안전 제한값 복원"""
        try:
            disp_limit = self.settings_mgr.load_displacement_limit()
            if disp_limit > 0:
                self.ui.DisplaceLimitMax_doubleSpinBox.setValue(disp_limit)
                logger.info(f"변위 제한값 복원: {disp_limit} mm")
            
            force_limit = self.settings_mgr.load_force_limit()
            if force_limit > 0:
                self.ui.ForceLimitMax_doubleSpinBox.setValue(force_limit)
                logger.info(f"하중 제한값 복원: {force_limit} N")
        except Exception as e:
            logger.error(f"안전 제한값 복원 실패: {e}")

    def on_basic_test_start(self):
        logger.info("[TEST] 'Start' 버튼 클릭됨")
        
        self.data_handler.reset_guards()
        self.data_handler.capture_start_position()

        if not self.basic_test or not self.motor_manager.is_connected():
            ErrorHandler.show_not_connected_error("Motor", self)
            return
            
        if self.plot_service:
            try:
                success = self.plot_service.start_plotting()
                if not success:
                    logger.info("[TEST] PlotService 시작 취소됨.")
                    return 
            except Exception as e:
                logger.error(f"[TEST] PlotService 시작 실패: {e}")
                ErrorHandler.show_error(
                    "파일 오류", 
                    f"로그 파일을 시작할 수 없습니다:\n{e}",
                    self
                )
                return
        else:
            logger.warning("[TEST] PlotService가 초기화되지 않았습니다.")

        try:
            self.basic_test.start()
            logger.info("[TEST] BasicTest.start() 호출 완료")
        except Exception as e:
            logger.error(f"[TEST] BasicTest.start() 예외: {e}")

    def _stop_all_tests(self, reason="Unknown"):
        """[중앙 정지] 테스트, 모터, 플로팅, 온도 제어를 모두 중지"""
        logger.info(f"[TEST_CONTROL] 모든 작업 중지 시도. 사유: {reason}")
        
        # ===== 추가: 온도 제어 정지 =====
        self._stop_temp_control_safely()

        if self.motor_manager.is_connected():
            try:
                self.motor_manager.controller.stop_motor()
                logger.info("[TEST_CONTROL] 하드웨어 모터 정지 완료")
            except Exception as e:
                logger.error(f"[TEST_CONTROL] motor.stop_motor() 예외: {e}")

        if self.basic_test:
            try:
                self.basic_test.stop() 
            except Exception as e:
                logger.error(f"[TEST_CONTROL] basic_test.stop() 예외: {e}")

        if self.pretension_test:
            try:
                self.pretension_test.stop()
            except Exception as e:
                logger.error(f"[TEST_CONTROL] pretension_test.stop() 예외: {e}")
        
        if self.plot_service:
            try:
                self.plot_service.stop_plotting()
            except Exception as e:
                logger.error(f"[TEST_CONTROL] plot_service.stop_plotting() 예외: {e}")

    def on_basic_test_stop(self):
        """Test 패널의 Stop 버튼"""
        self._stop_all_tests(reason="사용자 Stop 버튼 클릭")
        
    def _force_initial_button_policy(self):
        # Motor
        if hasattr(self.ui, "Comconnect_pushButton"):
            self.ui.Comconnect_pushButton.setEnabled(True)
        if hasattr(self.ui, "Comdisconnect_pushButton"):
            self.ui.Comdisconnect_pushButton.setEnabled(False)
        # Load Cell
        if hasattr(self.ui, "Comconnect_pushButton_2"):
            self.ui.Comconnect_pushButton_2.setEnabled(True)
        if hasattr(self.ui, "Comdisconnect_pushButton_2"):
            self.ui.Comdisconnect_pushButton_2.setEnabled(False)
        # Temp Controller
        if hasattr(self.ui, "Comconnect_pushButton_3"):
            self.ui.Comconnect_pushButton_3.setEnabled(True)
        if hasattr(self.ui, "Comdisconnect_pushButton_3"):
            self.ui.Comdisconnect_pushButton_3.setEnabled(False)

    def _prepare_combo_for_placeholder(self, combo: QtWidgets.QComboBox):
        if not combo:
            return
        combo.setEditable(True)
        le = combo.lineEdit()
        if le:
            le.setReadOnly(True)
            le.setPlaceholderText(" ")

    def _init_com_ui(self):
        # Motor Baud
        if hasattr(self.ui, "Baud_comboBox"):
            self.ui.Baud_comboBox.clear()
            self.ui.Baud_comboBox.addItems(["9600", "19200", "38400", "57600", "115200"])
            
            # ===== 저장된 보드레이트 불러오기 =====
            saved_baudrate = self.settings_mgr.load_motor_baudrate()
            self.ui.Baud_comboBox.setCurrentText(str(saved_baudrate))

        # Load Cell Baud
        if hasattr(self.ui, "Baud_comboBox_2"):
            self.ui.Baud_comboBox_2.clear()
            self.ui.Baud_comboBox_2.addItems(["9600", "19200", "38400", "57600", "115200"])
            
            # ===== 저장된 보드레이트 불러오기 =====
            saved_baudrate = self.settings_mgr.load_loadcell_baudrate()
            self.ui.Baud_comboBox_2.setCurrentText(str(saved_baudrate))

        # Temp Controller Baud
        if hasattr(self.ui, "Baud_comboBox_3"):
            self.ui.Baud_comboBox_3.clear()
            self.ui.Baud_comboBox_3.addItems(["9600", "19200", "38400", "57600", "115200"])
            
            # ===== 저장된 보드레이트 불러오기 =====
            saved_baudrate = self.settings_mgr.load_temp_baudrate()
            self.ui.Baud_comboBox_3.setCurrentText(str(saved_baudrate))

        self._prepare_combo_for_placeholder(getattr(self.ui, "Com_comboBox", None))
        self._prepare_combo_for_placeholder(getattr(self.ui, "Com_comboBox_2", None))
        self._prepare_combo_for_placeholder(getattr(self.ui, "Com_comboBox_3", None))

        self.refresh_com_ports()

        if hasattr(self.ui, "Comconnect_pushButton"):
            self.ui.Comconnect_pushButton.clicked.connect(self.on_com_connect_motor)
        if hasattr(self.ui, "Comdisconnect_pushButton"):
            self.ui.Comdisconnect_pushButton.clicked.connect(self.on_com_disconnect_motor)

        if hasattr(self.ui, "Comconnect_pushButton_2"):
            self.ui.Comconnect_pushButton_2.clicked.connect(self.on_com_connect_lc)
        if hasattr(self.ui, "Comdisconnect_pushButton_2"):
            self.ui.Comdisconnect_pushButton_2.clicked.connect(self.on_com_disconnect_lc)

        if hasattr(self.ui, "Comconnect_pushButton_3"):
            self.ui.Comconnect_pushButton_3.clicked.connect(self.on_com_connect_temp)
        if hasattr(self.ui, "Comdisconnect_pushButton_3"):
            self.ui.Comdisconnect_pushButton_3.clicked.connect(self.on_com_disconnect_temp)

        for name in ("Comrefresh_pushButton", "Comrefresh_pushButton_2", "Comrefresh_pushButton_3"):
            btn = getattr(self.ui, name, None)
            if btn:
                btn.clicked.connect(lambda _=False, n=name: self.on_com_refresh_clicked(n))

        self._force_initial_button_policy()

        # ===== 저장된 포트 복원 =====
        self._restore_saved_ports()

    def _restore_saved_ports(self):
        """저장된 COM 포트 복원"""
        try:
            # Motor 포트 복원
            motor_port = self.settings_mgr.load_motor_port()
            if motor_port and hasattr(self.ui, "Com_comboBox"):
                idx = self.ui.Com_comboBox.findText(motor_port)
                if idx >= 0:
                    self.ui.Com_comboBox.setCurrentIndex(idx)
                    logger.info(f"Motor 포트 복원: {motor_port}")
            
            # Loadcell 포트 복원
            lc_port = self.settings_mgr.load_loadcell_port()
            if lc_port and hasattr(self.ui, "Com_comboBox_2"):
                idx = self.ui.Com_comboBox_2.findText(lc_port)
                if idx >= 0:
                    self.ui.Com_comboBox_2.setCurrentIndex(idx)
                    logger.info(f"Loadcell 포트 복원: {lc_port}")
            
            # Temp 포트 복원
            temp_port = self.settings_mgr.load_temp_port()
            if temp_port and hasattr(self.ui, "Com_comboBox_3"):
                idx = self.ui.Com_comboBox_3.findText(temp_port)
                if idx >= 0:
                    self.ui.Com_comboBox_3.setCurrentIndex(idx)
                    logger.info(f"Temp 포트 복원: {temp_port}")
        
        except Exception as e:
            logger.error(f"포트 복원 실패: {e}")

    def refresh_com_ports(self):
        ports = [p.device for p in list_ports.comports()]
        logger.debug(f"[REFRESH] start, found ports: {ports}")

        def _fill(combo: QtWidgets.QComboBox, tag: str):
            if combo is None or not isinstance(combo, QtWidgets.QComboBox):
                logger.warning(f"[REFRESH] {tag} combo MISSING")
                return

            prev = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            if ports:
                combo.addItems(ports)
                if prev in ports:
                    combo.setCurrentText(prev)
            combo.blockSignals(False)

        motor_combo = getattr(self.ui, "Com_comboBox", None)
        loadcell_combo = getattr(self.ui, "Com_comboBox_2", None)
        temp_combo = getattr(self.ui, "Com_comboBox_3", None)
        _fill(motor_combo, "Motor")
        _fill(loadcell_combo, "LoadCell")
        _fill(temp_combo, "Temp")

    def on_com_refresh_clicked(self, source_name="Comrefresh_pushButton"):
        btn = getattr(self.ui, source_name, None)
        if btn:
            btn.setEnabled(False)
            old = btn.text()
            btn.setText("Scanning...")
        try:
            self.refresh_com_ports()
        finally:
            if btn:
                btn.setText(old)
                btn.setEnabled(True)

    # ========================
    # Motor Connect / Disconnect
    # ========================
    def on_com_connect_motor(self):
        c1 = getattr(self.ui, "Com_comboBox", QtWidgets.QComboBox())
        port_text = (c1.currentText() or "").strip()
        
        if not port_text:
            self.refresh_com_ports()
            ErrorHandler.show_info(
                "포트 선택 필요", 
                "포트를 선택하거나 장치를 연결하세요.",
                self
            )
            if hasattr(self.ui, "progressBar"): 
                self.ui.progressBar.setValue(0)
            return

        try:
            baud_cb = getattr(self.ui, "Baud_comboBox", None)
            baud = int(baud_cb.currentText() or str(motor_cfg.DEFAULT_BAUDRATE)) if baud_cb else motor_cfg.DEFAULT_BAUDRATE
        except ValueError:
            baud = motor_cfg.DEFAULT_BAUDRATE

        # 클라이언트 객체 생성
        self.motor_client = ModbusSerialClient(
            port=port_text, 
            baudrate=baud, 
            bytesize=8, 
            parity='N', 
            stopbits=1, 
            timeout=motor_cfg.DEFAULT_TIMEOUT
        )

        ok, err = False, None
        try:
            if self.motor_client.connect():
                logger.info("[MOTOR] Handshake 시도...")
                
                chk = self.motor_client.read_holding_registers(
                    address=motor_cfg.ADDR_POSITION_HI, 
                    count=2, 
                    device_id=motor_cfg.DEFAULT_UNIT_ID
                )
                
                if chk.isError():
                    ok = False
                    err = f"Modbus Error: {chk}"
                    logger.error(f"[MOTOR] Handshake 실패: {chk}")
                    self.motor_client.close()
                else:
                    ok = True
                    logger.info(f"[MOTOR] Handshake 성공. Registers: {chk.registers}")
            else:
                ok = False

        except Exception as e:
            err = str(e)
            ok = False
            if self.motor_client:
                self.motor_client.close()

        logger.info(f"[MOTOR] Connect → {port_text} @ {baud} : {ok}")

        if ok:
            success = self.motor_manager.start_service(
                client=self.motor_client,
                unit_id=motor_cfg.DEFAULT_UNIT_ID,
                interval_ms=self.monitor_interval_ms
            )
            
            if success:
                # 하위 호환성 유지
                self.motor = self.motor_manager.controller
                self.motor_monitor = self.motor_manager.monitor
                
                self.speed_controller.set_motor(self.motor)
                self.basic_test = BasicTest(self.motor, self.speed_controller.get_run_speed)

                if PretensionTest:
                    self.pretension_test = PretensionTest(
                        motor_service=self.motor,
                        loadcell_service=self.loadcell_service,
                        data_handler=self.data_handler
                    )
                    self.pretension_test.finished.connect(
                        lambda: ErrorHandler.show_success(
                            "완료", 
                            "초기 하중 설정 및 모터 0점 설정",
                            self
                        )
                    )

                # ===== 연결 성공 시 포트/보드레이트 저장 =====
                self.settings_mgr.save_motor_port(port_text)
                self.settings_mgr.save_motor_baudrate(baud)

                if hasattr(self.ui, "progressBar"): 
                    self.ui.progressBar.setValue(100)
                
                ErrorHandler.show_success(
                    "연결 성공",
                    f"모터 연결 성공: {port_text} @ {baud}",
                    self
                )
                
                if hasattr(self.ui, "Comdisconnect_pushButton"):
                    self.ui.Comdisconnect_pushButton.setEnabled(True)
                if hasattr(self.ui, "Comconnect_pushButton"):
                    self.ui.Comconnect_pushButton.setEnabled(False)
            else:
                logger.error("MotorManager 서비스 시작 실패")
                if hasattr(self.ui, "progressBar"): 
                    self.ui.progressBar.setValue(0)
                ErrorHandler.show_warning(
                    "서비스 실패",
                    f"모터 서비스 시작 실패",
                    self
                )
        else:
            logger.error(f"모터 연결 실패: {port_text} @ {baud}\n{err or ''}")
            if hasattr(self.ui, "progressBar"): 
                self.ui.progressBar.setValue(0)
            
            ErrorHandler.show_connection_error("Motor", port_text, err or "", self)
            
            if hasattr(self.ui, "Comconnect_pushButton"):
                self.ui.Comconnect_pushButton.setEnabled(True)
            if hasattr(self.ui, "Comdisconnect_pushButton"):
                self.ui.Comdisconnect_pushButton.setEnabled(False)
            
            self.motor = None
            self.basic_test = None
            self.speed_controller.set_motor(None)

    def on_com_disconnect_motor(self):
        self._stop_all_tests(reason="모터 연결 해제")

        self.motor_manager.stop_service()
        
        # 하위 호환성 유지
        self.motor = None
        self.motor_monitor = None
        self.basic_test = None
        self.pretension_test = None
        self.speed_controller.set_motor(None)

        if self.motor_client:
            try:
               self.motor_client.close()
            except Exception as e:
                logger.error(f"클라이언트 종료 실패: {e}")
            finally:
                self.motor_client = None

        if hasattr(self.ui, "progressBar"): 
            self.ui.progressBar.setValue(0)
        
        logger.info("모터 연결을 해제했습니다.")
        ErrorHandler.show_info("연결 해제", "모터 연결을 해제했습니다.", self)
        
        if hasattr(self.ui, "Comconnect_pushButton"):
            self.ui.Comconnect_pushButton.setEnabled(True)
        if hasattr(self.ui, "Comdisconnect_pushButton"):
            self.ui.Comdisconnect_pushButton.setEnabled(False)

    # ========================
    # Load Cell Connect / Disconnect
    # ========================
    def on_com_connect_lc(self):
        cb = getattr(self.ui, "Com_comboBox_2", None)
        bcb = getattr(self.ui, "Baud_comboBox_2", None)
        port_text = ((cb.currentText() if cb else "") or "").strip()

        if not port_text:
            self.refresh_com_ports()
            ErrorHandler.show_info(
                "포트 선택 필요", 
                "포트를 선택하거나 장치를 연결하세요.",
                self
            )
            if hasattr(self.ui, "progressBar_2"): 
                self.ui.progressBar_2.setValue(0)
            return

        try:
            baud = int(bcb.currentText() or str(loadcell_cfg.DEFAULT_BAUDRATE)) if bcb else loadcell_cfg.DEFAULT_BAUDRATE
        except ValueError:
            baud = loadcell_cfg.DEFAULT_BAUDRATE

        # ===== Serial 객체 생성 (Main.py에서 직접 관리) =====
        self.loadcell_serial = serial.Serial()
        self.loadcell_serial.port = port_text
        self.loadcell_serial.baudrate = baud
        self.loadcell_serial.parity = loadcell_cfg.DEFAULT_PARITY
        self.loadcell_serial.bytesize = loadcell_cfg.DEFAULT_BYTESIZE
        self.loadcell_serial.stopbits = loadcell_cfg.DEFAULT_STOPBITS
        self.loadcell_serial.timeout = loadcell_cfg.DEFAULT_TIMEOUT

        ok = False
        
        try:
            # ===== 포트 열기 =====
            self.loadcell_serial.open()
            logger.info(f"[LC] 포트 열림: {port_text} @ {baud}")
            logger.info(f"[LC] Connect → {port_text} @ {baud} : {ok}")

            # ===== Handshake 검증 =====
            from Controller_Loadcell import verify_loadcell_connection
            ok, err = verify_loadcell_connection(self.loadcell_serial)

        except serial.SerialException as e:
            err = f"시리얼 포트 오류: {e}"
            ok = False
            logger.error(f"[LC] 연결 실패: {err}")
            if self.loadcell_serial.is_open:
                self.loadcell_serial.close()
    
        except Exception as e:
            err = f"예상치 못한 오류: {e}"
            ok = False
            logger.error(f"[LC] 연결 실패: {err}", exc_info=True)
            if self.loadcell_serial and self.loadcell_serial.is_open:
                self.loadcell_serial.close()

        logger.info(f"[LC] Connect → {port_text} @ {baud} : {ok}")

        if ok:
            # ===== Manager 시작 (Serial 객체 전달) =====
            success = self.loadcell_manager.start_service(
            serial_port=self.loadcell_serial,
            interval_ms=self.monitor_interval_ms
        )
            
            if success:
                # 하위 호환성 유지
                self.loadcell_service = self.loadcell_manager.controller
                self.lc_monitor = self.loadcell_manager.monitor

                # ===== 연결 성공 시 포트/보드레이트 저장 =====
                self.settings_mgr.save_loadcell_port(port_text)
                self.settings_mgr.save_loadcell_baudrate(baud)

                if hasattr(self.ui, "progressBar_2"): 
                    self.ui.progressBar_2.setValue(100)
                
                ErrorHandler.show_success(
                    "연결 성공",
                    f"로드셀 연결 성공: {port_text} @ {baud}",
                    self
                )
                
                if hasattr(self.ui, "Comdisconnect_pushButton_2"):
                    self.ui.Comdisconnect_pushButton_2.setEnabled(True)
                if hasattr(self.ui, "Comconnect_pushButton_2"):
                    self.ui.Comconnect_pushButton_2.setEnabled(False)
            else:
                logger.error("LoadcellManager 서비스 시작 실패")
                self.loadcell_serial.close()
                self.loadcell_serial = None
                
                if hasattr(self.ui, "progressBar_2"): 
                    self.ui.progressBar_2.setValue(0)
                
                ErrorHandler.show_warning(
                    "서비스 실패",
                    f"로드셀 서비스 시작 실패",
                    self
                )
        else:
            logger.error(f"[LC] Handshake 실패: {port_text} @ {baud}")
            if hasattr(self.ui, "progressBar_2"): 
                self.ui.progressBar_2.setValue(0)
        
            ErrorHandler.show_connection_error("Loadcell", port_text, err or "", self)
            
            if hasattr(self.ui, "Comconnect_pushButton_2"):
                self.ui.Comconnect_pushButton_2.setEnabled(True)
            if hasattr(self.ui, "Comdisconnect_pushButton_2"):
                self.ui.Comdisconnect_pushButton_2.setEnabled(False)
            
            self.loadcell_serial = None

    def on_com_disconnect_lc(self):
        self._stop_all_tests(reason="로드셀 연결 해제")

        self.loadcell_manager.stop_service()
        
        # 하위 호환성 유지
        self.loadcell_service = None
        self.lc_monitor = None
            
        # ===== Serial 객체 종료 (Main.py에서 직접 관리) =====
        if self.loadcell_serial:
            try:
                self.loadcell_serial.close()
                logger.info("[LC] Serial 포트 종료 완료")
            except Exception as e:
                logger.error(f"Serial 포트 종료 실패: {e}")
            finally:
                self.loadcell_serial = None
            
        if hasattr(self.ui, "progressBar_2"):
            self.ui.progressBar_2.setValue(0)

        logger.info("로드셀 연결을 해제했습니다.")
        ErrorHandler.show_info("연결 해제", "로드셀 연결을 해제했습니다.", self)

        if hasattr(self.ui, "Comconnect_pushButton_2"):
            self.ui.Comconnect_pushButton_2.setEnabled(True)
        if hasattr(self.ui, "Comdisconnect_pushButton_2"):
            self.ui.Comdisconnect_pushButton_2.setEnabled(False)

    # ========================
    # Temp Controller Connect / Disconnect
    # ========================
    def on_temp_start(self):
        """온도 Start 버튼 클릭 시 호출"""
        logger.info("=" * 80)
        logger.info("[Main] 온도 Start 버튼 클릭됨")
        logger.info("=" * 80)
        try:
            if self.temp_manager:
                logger.info("[Main] TempManager.start_control() 호출 시작")
                success = self.temp_manager.start_control()  # ===== 변경 =====
                logger.info(f"[Main] TempManager.start_control() 결과: {success}")
                
                if success:
                    # 버튼 상태 변경
                    self.ui.temp_start_btn.setEnabled(False)
                    self.ui.temp_stop_btn.setEnabled(True)
            else:
                logger.error("[Main] TempManager가 None입니다.")
                ErrorHandler.show_not_connected_error("Temp Controller", self)
        except Exception as e:
            logger.error(f"[Main] 온도 제어 시작 실패: {e}", exc_info=True)
            ErrorHandler.show_error(
                "오류",
                f"온도 제어 시작 중 오류 발생:\n{e}",
                self
            )
    
    def on_temp_stop(self):
        """온도 Stop 버튼 클릭 시 호출"""
        logger.info("=" * 80)
        logger.info("[Main] 온도 Stop 버튼 클릭됨")
        logger.info("=" * 80)
        
        if self.temp_manager:
            success = self.temp_manager.stop_control()  # ===== 변경 =====
            
            if success:
                # 버튼 상태 변경
                if hasattr(self.ui, "temp_stop_btn"):
                    self.ui.temp_stop_btn.setEnabled(False)
                if hasattr(self.ui, "temp_start_btn"):
                    self.ui.temp_start_btn.setEnabled(True)
        
        # 버튼 상태 변경
        if hasattr(self.ui, "temp_stop_btn"):
            self.ui.temp_stop_btn.setEnabled(False)
        if hasattr(self.ui, "temp_start_btn"):
            self.ui.temp_start_btn.setEnabled(True)
    
    def on_com_connect_temp(self):
        """온도 제어기 연결"""
        c3 = getattr(self.ui, "Com_comboBox_3", QtWidgets.QComboBox())
        port_text = (c3.currentText() or "").strip()
        
        if not port_text:
            self.refresh_com_ports()
            ErrorHandler.show_info(
                "포트 선택 필요", 
                "포트를 선택하거나 장치를 연결하세요.",
                self
            )
            return

        try:
            baud_cb = getattr(self.ui, "Baud_comboBox_3", None)
            baud = int(baud_cb.currentText() or str(temp_cfg.DEFAULT_BAUDRATE)) if baud_cb else temp_cfg.DEFAULT_BAUDRATE
        except ValueError:
            baud = temp_cfg.DEFAULT_BAUDRATE

        self.temp_client = ModbusSerialClient(
            port=port_text, 
            baudrate=baud, 
            bytesize=8, 
            parity=temp_cfg.DEFAULT_PARITY, 
            stopbits=1, 
            timeout=temp_cfg.DEFAULT_TIMEOUT
        )

        ok, err = False, None

        try:
            if self.temp_client.connect():
                logger.info(f"[TEMP] 연결 시도 중... (Port: {port_text})")
                
                chk = self.temp_client.read_input_registers(address=0x0066, count=1, device_id=1)
                
                if chk.isError():
                    ok = False
                    err = f"Modbus 응답 에러: {chk}"
                    logger.error(f"[TEMP] Handshake 실패: {err}")
                    self.temp_client.close()
                else:
                    ok = True
                    logger.info(f"[TEMP] Handshake 성공. 데이터: {chk.registers}")
            else:
                ok = False
                err = "포트를 열 수 없습니다."

        except Exception as e:
            ok = False
            err = str(e)
            if self.temp_client:
                self.temp_client.close()

        if ok:
            if hasattr(self, 'temp_manager'):
                success = self.temp_manager.start_service(
                    self.temp_client, 
                    monitor_cfg.DEFAULT_INTERVAL_MS
                )
                
                if success:
                    logger.info(f"[TEMP] 연결 성공: {port_text}")
                    
                    # ===== 연결 성공 시 포트/보드레이트 저장 =====
                    self.settings_mgr.save_temp_port(port_text)
                    self.settings_mgr.save_temp_baudrate(baud)
                    
                    ErrorHandler.show_success(
                        "연결 성공", 
                        f"온도 제어기 연결 성공: {port_text}",
                        self
                    )
                    
                    if hasattr(self.ui, "Comdisconnect_pushButton_3"):
                        self.ui.Comdisconnect_pushButton_3.setEnabled(True)
                    if hasattr(self.ui, "Comconnect_pushButton_3"):
                        self.ui.Comconnect_pushButton_3.setEnabled(False)
                else:
                    logger.error("TempManager 서비스 시작 실패")
                    ErrorHandler.show_warning(
                        "서비스 실패", 
                        "온도 제어 서비스 시작 실패",
                        self
                    )
        else:
            logger.error(f"[TEMP] 연결 실패: {err}")
            ErrorHandler.show_connection_error("Temp Controller", port_text, err, self)
            self.temp_client = None

    def on_com_disconnect_temp(self):
        """온도 제어기 연결 해제 (제어 정지 포함)"""
        
        # ===== 추가: 제어 정지 =====
        logger.info("[TEMP_DISCONNECT] 연결 해제 전 제어 정지")
        self._stop_temp_control_safely()
        
        # 약간의 대기 시간 (Modbus 명령 완료 대기)
        QtCore.QTimer.singleShot(200, self._finalize_temp_disconnect)
    
    def _finalize_temp_disconnect(self):
        """온도 제어기 연결 해제 완료"""
        try:
            if self.temp_client:
                self.temp_client.close()
                logger.info("[TEMP_DISCONNECT] Modbus 클라이언트 종료 완료")
        except Exception as e:
            logger.error(f"[TEMP_DISCONNECT] close 예외: {e}")
        
        self.temp_client = None
        self.temp_manager.stop_service()

        logger.info("온도 제어기 연결을 해제했습니다.")
        ErrorHandler.show_info("연결 해제", "온도 제어기 연결을 해제했습니다.", self)

        if hasattr(self.ui, "Comconnect_pushButton_3"):
            self.ui.Comconnect_pushButton_3.setEnabled(True)
        if hasattr(self.ui, "Comdisconnect_pushButton_3"):
            self.ui.Comdisconnect_pushButton_3.setEnabled(False)
        
        # UI 버튼 상태도 초기화
        if hasattr(self.ui, "temp_start_btn"):
            self.ui.temp_start_btn.setEnabled(True)
        if hasattr(self.ui, "temp_stop_btn"):
            self.ui.temp_stop_btn.setEnabled(False)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    
    try:
        app_font = QtGui.QFont("Pretendard", 10, QtGui.QFont.DemiBold)
    except Exception:
        app_font = QtGui.QFont("Arial", 10, QtGui.QFont.Bold)
    app.setFont(app_font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
