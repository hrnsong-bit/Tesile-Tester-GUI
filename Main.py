# Main.py
import pymodbus
import sys, time, re
import os

# 로깅 임포트
import logging
import Logging_Config

# 로깅 설정 실행
Logging_Config.setup_logging()

# Main.py 자신의 로거 가져오기
logger = logging.getLogger(__name__)

logger.info(f"실행 중인 Python 경로: {sys.executable}")
logger.info(f"실행 중인 Python 버전: {sys.version}")
logger.info(f"Using pymodbus version: {pymodbus.__version__}")


import serial

from serial.tools import list_ports
from PyQt5 import QtWidgets, QtCore, QtGui
from GUI import Ui_MainWindow
from Controller_motor import MotorService
from Controller_Loadcell import LoadcellService
from pymodbus.client.serial import ModbusSerialClient
from Manager_temp import TempManager
from Basic_Test import BasicTest
from Ui_Binding import bind_main_signals
from Monitor_motor import MotorMonitor
from Monitor_loadcell import LoadcellMonitor
from Plot_Service import PlotService

try:
    #  TabDICUTM 추가 임포트
    from Data_Repack import TabDICUTM, TabMultiCompare, TabPreprocessor
except ImportError as e:
    logger.error(f"Data_Repack.py 임포트 실패: {e}. matplotlib, pandas, numpy가 설치되었는지 확인하세요.")
    # 실패 시 앱이 죽지 않도록 임시 클래스로 대체
    TabDICUTM = QtWidgets.QWidget
    TabMultiCompare = QtWidgets.QWidget
    TabPreprocessor = QtWidgets.QWidget
# =================================================================

# 신규 모듈 임포트
from Speed_Controller import SpeedController
from Data_Handler import DataHandler

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
            # self.ui.hz_spinBox 로 참조 변경
            hz_val = self.ui.hz_spinBox.value() 
            if hz_val <= 0:
                QtWidgets.QMessageBox.warning(self, "오류", "Frequency는 0보다 커야 합니다.")
                return
            
            # Hz를 ms로 변환하여 저장
            self.monitor_interval_ms = int(1000 / hz_val)
            logger.info(f"[HZ] Monitor interval set to {self.monitor_interval_ms} ms ({hz_val} Hz)")

            # 이미 실행 중인 모니터가 있다면, 타이머 간격 즉시 업데이트
            if self.motor_monitor and hasattr(self.motor_monitor, 'timer') and self.motor_monitor.timer.isActive():
                self.motor_monitor.timer.setInterval(self.monitor_interval_ms)
                logger.info("[HZ] Motor monitor interval updated.")
            
            if self.lc_monitor and hasattr(self.lc_monitor, 'timer') and self.lc_monitor.timer.isActive():
                self.lc_monitor.timer.setInterval(self.monitor_interval_ms)
                logger.info("[HZ] Loadcell monitor interval updated.")

            QtWidgets.QMessageBox.information(self, "Frequency Set", f"모니터링 주파수가 {hz_val} Hz ({self.monitor_interval_ms} ms)로 설정되었습니다.\n(적용은 다음 연결 또는 즉시)")

        except Exception as e:
            logger.error(f"[HZ] Error setting frequency: {e}")
            QtWidgets.QMessageBox.warning(self, "오류", f"주파수 설정 중 오류 발생: {e}")
            
    # ========================
    # 컨트롤러 슬롯
    # ========================

    def on_lc_set_clicked(self):
        try:
            # 서비스 객체가 있는지 확인
            if not self.loadcell_service:
                logger.error("[ERR] 로드셀 서비스가 초기화되지 않았습니다.")
                return

            logger.info(f"[INFO] CDL Zeroing 요청...")
            self.loadcell_service.zero_position() # <- 서비스의 메서드 호출
        
        except Exception as e:
            logger.error(f"[ERR] Zeroing 실패: {e}")

    def on_zero_encoder_clicked(self):
        if self.motor:
            self.motor.zero_position()
        else:
            logger.error("[ERR] 모터가 연결되지 않아 0점 설정을 할 수 없습니다.")

    # ========== Reset 버튼 클릭 시 실행될 함수 ==========
    def on_reset_clicked(self):
        """Reset 버튼 클릭 시: 가드 리셋 + 모터 원점 복귀"""
        logger.info("[Reset] 버튼 클릭됨")

        # 1. 기존 기능: 소프트웨어 가드(멈춤 신호) 및 UI 라벨 초기화
        self.data_handler.reset_all_guards()
        self.data_handler.reset_ui_labels()
        
        # 2. 추가 기능: 모터 물리적 원점(0) 이동
        if self.motor:
            # 이동 속도 설정 (안전하게 10 rps)
            safe_speed_rps = 10 
            target_pos = 0 # 0 위치로 이동
            
            logger.info(f"[Reset] 가드 리셋 완료. 모터를 원점({target_pos})으로 이동합니다.")
            
            # Controller_motor.py에 있는 move_to_absolute 호출
            # 인자: (목표펄스, 속도rps)
            success = self.motor.move_to_absolute(target_pos, safe_speed_rps)
            
            if success:
                QtWidgets.QMessageBox.information(self, "Reset", "모터가 원점(0)으로 이동합니다.")
            else:
                QtWidgets.QMessageBox.warning(self, "Reset", "모터 이동 명령 실패 (통신 오류)")
        else:
             QtWidgets.QMessageBox.warning(self, "Reset", "(모터가 연결되지 않아 이동은 생략합니다.)")

    # ========== Pretension 관련 슬롯 함수 추가 ==========
    def on_pretension_start(self):
        if not self.pretension_test or not self.motor:
            QtWidgets.QMessageBox.warning(self, "오류", "모터가 연결되지 않았거나 Pretension 기능이 준비되지 않았습니다.")
            return

        # 1. UI에서 값 읽어오기
        speed_val_um = self.ui.tension_speed_spinBox.value() # um/sec
        target_load_n = self.ui.tension_force_spinBox.value() # N

        # 2. 단위 변환 (um/sec -> rps)
        # 스크류 리드가 0.01mm(10um)라고 가정 시: 1회전 = 10um 이동
        # rps = (목표속도 um/s) / 10
        rps_speed = speed_val_um / 10.0 
        
        # 3. 시작 명령 내리기
        self.pretension_test.start(target_speed_rps=rps_speed, target_load_n=target_load_n)

    def on_pretension_stop(self):
        if self.pretension_test:
            self.pretension_test.stop()


    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        try:
            self.plot_service = PlotService(
                self, 
                self.ui.graphicsView,
                ui=self.ui,
                temp_plot_widget=self.ui.temp_plot  # GUI.py에서 생성한 위젯
            )
            logger.info("PlotService 초기화 완료")
        except Exception as e:
            logger.error(f"PlotService 초기화 실패: {e}")
            self.plot_service = None
        
        self.temp_manager = TempManager(self.ui, plot_service=self.plot_service)

        if hasattr(self.ui, 'temp_set_btn'):
            self.ui.temp_set_btn.clicked.connect(self.temp_manager.apply_settings)

        try:
            if self.ui.data_tab_layout.count() > 0:
                item = self.ui.data_tab_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                    logger.debug("Data 탭의 placeholder 라벨 제거 완료")
        except Exception as e:
            logger.warning(f"Data 탭 placeholder 제거 실패: {e}")

        # 탭 인스턴스 생성 (SS Curve Generator 복구)
        self.ss_curve_widget = TabDICUTM()          # <-- 복구된 탭
        self.preprocessor_widget = TabPreprocessor()
        self.multi_compare_widget = TabMultiCompare()

        # 3. "Data" 탭 내부에 새로 QTabWidget을 생성
        self.data_sub_tabs = QtWidgets.QTabWidget()
        
        #  새 QTabWidget에 세 개의 위젯(탭)을 추가
        self.data_sub_tabs.addTab(self.ss_curve_widget, "SS Curve Generator")
        self.data_sub_tabs.addTab(self.preprocessor_widget, "CSV Preprocessor")
        self.data_sub_tabs.addTab(self.multi_compare_widget, "Multi Compare") 

        # 5. GUI.py의 data_tab_layout에 이 QTabWidget을 추가
        self.ui.data_tab_layout.addWidget(self.data_sub_tabs)
        
        logger.info("Data 탭에 SS Curve Gen, CSV Preprocessor, Multi Compare 서브 탭 삽입 완료")

        # PlotService 초기화 (UI가 설정된 직후)
        try:
            # PlotService 생성 시 self (MainWindow)를 부모로 전달
            self.plot_service = PlotService(self, self.ui.graphicsView)
            logger.info("PlotService 초기화 완료")
        except Exception as e:
            logger.error(f"PlotService 초기화 실패: {e}")
            self.plot_service = None # 실패 시 None으로 유지
        
            
        
        # ================================================
        # Hz UI 연결 (생성은 GUI.py가 담당)
        # ================================================
        
        # 1. Hz 기본값 저장 (10 Hz -> 100 ms)
        self.monitor_interval_ms = int(1000 / self.ui.hz_spinBox.value()) 
        
        # 2. 'Set' 버튼 시그널 연결
        if hasattr(self.ui, 'hz_set_pushButton'):
            self.ui.hz_set_pushButton.clicked.connect(self._on_set_hz)
        # ================================================

        #LoadCell 영점 설정 버튼 시그널 연결
        self.ui.Load0_pushButton.clicked.connect(self.on_lc_set_clicked)

        # 내부 상태
        self.motor_client = None      # 모터용 ModbusSerialClient
        self.motor = None           # 모터용 MotorService (연결 시 생성)
        self.loadcell_service = LoadcellService() # <- LoadcellService 객체 생성
        self.motor_monitor = None     # 모터 모니터
        self.lc_monitor = None        # 로드셀 모니터
        
        # Temp Controller Client
        self.temp_client = None 

        # 리팩토링: 서비스 클래스 생성
        # 스크류 사양 (lead_mm_per_rev = 0.01 mm/rev)
        self.speed_controller = SpeedController(ui=self.ui, lead_mm_per_rev=0.01)
        self.data_handler = DataHandler(
            ui=self.ui, 
            plot_service=self.plot_service, 
            stop_all_tests_callback=self._stop_all_tests
        )

        # Pretension 객체 초기화 변수
        self.pretension_test = None

        # 스핀박스
        try:
            self.ui.Jog_spinBox.setSuffix("")
            self.ui.MotorSpeed_spinBox.setSuffix("")
        except Exception:
            pass

        # === COM UI 초기화(보드레이트/포트 채우기, 버튼 연결) ===
        self._init_com_ui()

        # 시작 시 UI 요소 비활성화
        self.ui.Setjogspeed_pushButton.setEnabled(False)
        self.ui.Jog_spinBox.setEnabled(False)
        self.ui.MotorSpeed_spinBox.setEnabled(False)
        self.ui.Setmotorspeed_pushButton.setEnabled(False)
        
        self.basic_test = None # <- None으로 초기화 (연결 시 생성)

        bind_main_signals(self.ui, self)
        logger.info("초기화 및 시그널 바인딩 완료")

        # Test Start 버튼을 우리 래퍼에 바인딩(기존 연결 제거 후 재연결)
        start_btn = getattr(self.ui, "Basicteststart_pushButton", None)
        if start_btn:
            try:
                start_btn.clicked.disconnect()  # 기존 연결 전부 해제
            except Exception:
                pass
            start_btn.clicked.connect(self.on_basic_test_start)  # 가드 리셋 래퍼로 연결

        # Test Stop 버튼도 중앙 정지 함수로 연결
        stop_btn = getattr(self.ui, "Basicteststop_pushButton", None)
        if stop_btn:
            try:
                stop_btn.clicked.disconnect()
            except Exception:
                pass
            stop_btn.clicked.connect(self.on_basic_test_stop) # 중앙 정지 함수로 연결

        # ========== 수정됨: Reset 버튼 연결 ==========
        # Reset 버튼을 우리가 만든 on_reset_clicked 함수에 연결합니다.
        reset_btn = getattr(self.ui, "Basictestreset_pushButton", None)
        if reset_btn:
            try:
                reset_btn.clicked.disconnect() # 기존 연결 해제
            except Exception:
                pass
            reset_btn.clicked.connect(self.on_reset_clicked) # 새 함수 연결

        # ========== Pretension 버튼 연결 ==========
        if hasattr(self.ui, "tension_start_pushButton"):
            self.ui.tension_start_pushButton.clicked.connect(self.on_pretension_start)
        if hasattr(self.ui, "tension_stop_pushButton"):
            self.ui.tension_stop_pushButton.clicked.connect(self.on_pretension_stop)


        # 정책 강제: 시작 시 Connect=ON, Disconnect=OFF (모터/로드셀 모두)
        self._force_initial_button_policy()
        QtCore.QTimer.singleShot(0, self._force_initial_button_policy)

    # ========================
    # 변위 가드 리셋 & 테스트 스타트 래퍼
    # ========================
    
    def on_basic_test_start(self):
        logger.info("[TEST] 'Start' 버튼 클릭됨")
        
        # DataHandler의 메서드 호출
        self.data_handler.reset_all_guards()
        self.data_handler.capture_start_position()

        # 모터 및 테스트 객체가 준비되었는지 확인
        if not self.basic_test or not self.motor:
            logger.warning("[TEST] BasicTest 또는 Motor가 초기화되지 않았습니다. 모터 연결을 확인하세요.")
            QtWidgets.QMessageBox.warning(self, "오류", "모터가 연결되지 않아 테스트를 시작할 수 없습니다.")
            return
            
        # 플롯 서비스 시작
        if self.plot_service:
            try:
                success = self.plot_service.start_plotting()
                if not success:
                    logger.info("[TEST] PlotService 시작 취소됨. 테스트를 시작하지 않습니다.")
                    return 
            except Exception as e:
                logger.error(f"[TEST] PlotService 시작 실패: {e}")
                QtWidgets.QMessageBox.critical(self, "파일 오류", f"로그 파일을 시작할 수 없습니다:\n{e}")
                return
        else:
            logger.warning("[TEST] PlotService가 초기화되지 않았습니다. (그래프 없이 진행)")

        try:
            self.basic_test.start()
            logger.info("[TEST] BasicTest.start() 호출 (가드 리셋 완료)")
        except Exception as e:
            logger.error(f"[TEST] BasicTest.start() 예외: {e}")

    # 중앙정지 함수
    def _stop_all_tests(self, reason="Unknown"):
        """[중앙 정지] 테스트, 모터, 플로팅을 모두 중지시킵니다."""
        logger.info(f"[TEST_CONTROL] 모든 작업 중지 시도. 사유: {reason}")
        
        #  '하드웨어' 모터부터 무조건 정지
        if self.motor:
            try:
                self.motor.stop_motor() # 강제 정지 명령 (Command 6)
                logger.info("[TEST_CONTROL] 하드웨어 모터 정지 명령 전송 완료")
            except Exception as e:
                logger.error(f"[TEST_CONTROL] motor.stop_motor() 예외: {e}")

        # 2.소프트웨어 상태(플래그)들을 정리
        if self.basic_test:
            try:
                # running 플래그가 True였다면 False로 바꾸고 로그 남김
                self.basic_test.stop() 
            except Exception as e:
                logger.error(f"[TEST_CONTROL] basic_test.stop() 예외: {e}")

        if self.pretension_test:
            try:
                self.pretension_test.stop()
            except Exception as e:
                logger.error(f"[TEST_CONTROL] pretension_test.stop() 예외: {e}")
        
        # 3. 플로팅 서비스 중지
        if self.plot_service:
            try:
                self.plot_service.stop_plotting()
            except Exception as e:
                logger.error(f"[TEST_CONTROL] plot_service.stop_plotting() 예외: {e}")

    def on_basic_test_stop(self):
        """Test 패널의 Stop 버튼을 눌렀을 때 호출될 슬롯."""
        # 중앙 정지 함수를 호출
        self._stop_all_tests(reason="사용자 Stop 버튼 클릭")
        
    # ========================
    # 초기 버튼 정책 강제
    # ========================
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
        # [NEW] Temp Controller
        if hasattr(self.ui, "Comconnect_pushButton_3"):
            self.ui.Comconnect_pushButton_3.setEnabled(True)
        if hasattr(self.ui, "Comdisconnect_pushButton_3"):
            self.ui.Comdisconnect_pushButton_3.setEnabled(False)

    # ========================
    # 콤보를 '편집 가능 + 읽기 전용'으로 만들어 빈 선택(해제) 지원
    # ========================
    def _prepare_combo_for_placeholder(self, combo: QtWidgets.QComboBox):
        if not combo:
            return
        combo.setEditable(True)
        le = combo.lineEdit()
        if le:
            le.setReadOnly(True)
            le.setPlaceholderText(" ")
    # ========================
    # COM/BAUD UI 초기화
    # ========================
    def _init_com_ui(self):
        # Motor Baud (기본 9600)
        if hasattr(self.ui, "Baud_comboBox"):
            self.ui.Baud_comboBox.clear()
            self.ui.Baud_comboBox.addItems(["9600", "19200", "38400", "57600", "115200"])
            self.ui.Baud_comboBox.setCurrentText("9600")

        # Load Cell Baud (기본 9600)
        if hasattr(self.ui, "Baud_comboBox_2"):
            self.ui.Baud_comboBox_2.clear()
            self.ui.Baud_comboBox_2.addItems(["9600", "19200", "38400", "57600", "115200"])
            self.ui.Baud_comboBox_2.setCurrentText("9600")

        # [NEW] Temp Controller Baud (기본 9600)
        if hasattr(self.ui, "Baud_comboBox_3"):
            self.ui.Baud_comboBox_3.clear()
            self.ui.Baud_comboBox_3.addItems(["9600", "19200", "38400", "57600", "115200"])
            self.ui.Baud_comboBox_3.setCurrentText("9600") # TM4 출하사양 

        # 콤보를 '빈 선택' 가능하도록 준비
        self._prepare_combo_for_placeholder(getattr(self.ui, "Com_comboBox", None))
        self._prepare_combo_for_placeholder(getattr(self.ui, "Com_comboBox_2", None))
        self._prepare_combo_for_placeholder(getattr(self.ui, "Com_comboBox_3", None)) # [NEW]

        # 포트 스캔해서 콤보 채우기 (없으면 공란 유지)
        self.refresh_com_ports()

        # 버튼 시그널 (모터)
        if hasattr(self.ui, "Comconnect_pushButton"):
            self.ui.Comconnect_pushButton.clicked.connect(self.on_com_connect_motor)
        if hasattr(self.ui, "Comdisconnect_pushButton"):
            self.ui.Comdisconnect_pushButton.clicked.connect(self.on_com_disconnect_motor)

        # 버튼 시그널 (로드셀)
        if hasattr(self.ui, "Comconnect_pushButton_2"):
            self.ui.Comconnect_pushButton_2.clicked.connect(self.on_com_connect_lc)
        if hasattr(self.ui, "Comdisconnect_pushButton_2"):
            self.ui.Comdisconnect_pushButton_2.clicked.connect(self.on_com_disconnect_lc)

        # [NEW] 버튼 시그널 (Temp Controller)
        if hasattr(self.ui, "Comconnect_pushButton_3"):
            self.ui.Comconnect_pushButton_3.clicked.connect(self.on_com_connect_temp)
        if hasattr(self.ui, "Comdisconnect_pushButton_3"):
            self.ui.Comdisconnect_pushButton_3.clicked.connect(self.on_com_disconnect_temp)

        # Refresh 버튼(들) → 모든 콤보 갱신
        for name in ("Comrefresh_pushButton", "Comrefresh_pushButton_2", "Comrefresh_pushButton_3"):
            btn = getattr(self.ui, name, None)
            if btn:
                btn.clicked.connect(lambda _=False, n=name: self.on_com_refresh_clicked(n))

        self._force_initial_button_policy()

    # ========================
    # 포트 새로고침 (없으면 공란 유지)
    # ========================
    def refresh_com_ports(self):
        ports = [p.device for p in list_ports.comports()]
        logger.debug(f"[REFRESH] start, found ports: {ports}")

        def _fill(combo: QtWidgets.QComboBox, tag: str):
            if combo is None or not isinstance(combo, QtWidgets.QComboBox):
                logger.warning(f"[REFRESH] {tag} combo MISSING (None or wrong type)")
                return

            # 이전 선택 복구 포함
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
        temp_combo = getattr(self.ui, "Com_comboBox_3", None) # [NEW]
        _fill(motor_combo, "Motor")
        _fill(loadcell_combo, "LoadCell")
        _fill(temp_combo, "Temp") # [NEW]

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
            QtWidgets.QMessageBox.information(self, "포트 선택 필요", "포트를 선택하거나 장치를 연결하세요.")
            if hasattr(self.ui, "progressBar"): self.ui.progressBar.setValue(0)
            return

        try:
            baud_cb = getattr(self.ui, "Baud_comboBox", None)
            baud = int(baud_cb.currentText() or "9600") if baud_cb else 9600
        except ValueError:
            baud = 9600

        # 1. 클라이언트 객체 생성
        self.motor_client = ModbusSerialClient(port=port_text, baudrate=baud, bytesize=8, parity='N', stopbits=1, timeout=1.0)

        ok, err = False, None
        try:
            # 2. 물리적 연결 시도
            if self.motor_client.connect():
                #  ========== Handshake (데이터 읽기 시도) ==========
                logger.info("[MOTOR] Handshake 시도: 현재 위치(Address 117) 요청...")
                
                chk = self.motor_client.read_holding_registers(address=117, count=2, slave=1)
                
                if chk.isError():
                    ok = False
                    err = f"Modbus Error: {chk}"
                    logger.error(f"[MOTOR] Handshake 실패 (Modbus Error): {chk}")
                    self.motor_client.close() # 실패 시 닫기
                else:
                    # 데이터가 정상적으로 오면 성공
                    ok = True
                    logger.info(f"[MOTOR] Handshake 성공. Registers: {chk.registers}")
            else:
                ok = False

        except Exception as e:
            err = e
            ok = False
            if self.motor_client:
                self.motor_client.close()

        logger.info(f"[MOTOR] Connect → {port_text} @ {baud} : {ok}")

        if ok:
            # 3. 연결 성공 시: 서비스, 테스트, 모니터 객체 생성 및 주입
            
            self.motor = MotorService(client=self.motor_client, unit_id=1) 
            self.speed_controller.set_motor(self.motor)
            self.basic_test = BasicTest(self.motor, self.speed_controller.get_run_speed)

            #  Pretension 객체 생성 (모터, 로드셀, 데이터핸들러 주입)
            if PretensionTest:
                self.pretension_test = PretensionTest(
                    motor_service=self.motor,
                    loadcell_service=self.loadcell_service,
                    data_handler=self.data_handler
                )
                # 완료되면 메시지창 띄우기
                self.pretension_test.finished.connect(
                    lambda: QtWidgets.QMessageBox.information(self, "완료", "초기 하중 설정 및 모터 0점 설정")
                )

            if not self.motor_monitor:
                self.motor_monitor = MotorMonitor(
                    self.motor_client, 
                    self.data_handler.update_motor_position, 
                    self.monitor_interval_ms
                )

            if hasattr(self.ui, "progressBar"): self.ui.progressBar.setValue(100)
            QtWidgets.QMessageBox.information(self, "연결 성공",
                                              f"모터 연결 성공: {port_text} @ {baud}")
            if hasattr(self.ui, "Comdisconnect_pushButton"):
                self.ui.Comdisconnect_pushButton.setEnabled(True)
            if hasattr(self.ui, "Comconnect_pushButton"):
                self.ui.Comconnect_pushButton.setEnabled(False)
        else:
            logger.error(f"모터 연결 실패: {port_text} @ {baud}\n{err or ''}")
            if hasattr(self.ui, "progressBar"): self.ui.progressBar.setValue(0)
            QtWidgets.QMessageBox.warning(self, "연결 실패",
                                          f"모터 연결 실패: {port_text} @ {baud}\n{err or ''}")
            if hasattr(self.ui, "Comconnect_pushButton"):
                self.ui.Comconnect_pushButton.setEnabled(True)
            if hasattr(self.ui, "Comdisconnect_pushButton"):
                self.ui.Comdisconnect_pushButton.setEnabled(False)
            
            self.motor = None
            self.basic_test = None
            self.speed_controller.set_motor(None)

    def on_com_disconnect_motor(self):
        # 1. 중앙 정지 함수 호출 (테스트, 플로팅 등 모두 중지)
        self._stop_all_tests(reason="모터 연결 해제")

        # 2. 모니터 중지
        if self.motor_monitor:
            try:
                self.motor_monitor.stop() # QTimer 중지
            except Exception:
                pass
            self.motor_monitor = None
        
        # 3. 서비스 및 테스트 객체 해제
        self.motor = None
        self.basic_test = None
        self.pretension_test = None
        self.speed_controller.set_motor(None)

        # 4. 클라이언트 연결 해제
        if self.motor_client:
            try:
               self.motor_client.close()
            except Exception as e:
                logger.error(f"클라이언트 종료 실패: {e}")
            finally:
                self.motor_client = None

        # 라벨 초기화 (DataHandler에 위임)
        self.data_handler.reset_ui_labels()
        self.data_handler.reset_disp_guard()

        if hasattr(self.ui, "progressBar"): self.ui.progressBar.setValue(0)
        logger.info("모터 연결을 해제했습니다.")
        QtWidgets.QMessageBox.information(self, "연결 해제", "모터 연결을 해제했습니다.")
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
            QtWidgets.QMessageBox.information(self, "포트 선택 필요", "포트를 선택하거나 장치를 연결하세요.")
            if hasattr(self.ui, "progressBar_2"): self.ui.progressBar_2.setValue(0)
            return

        try:
            baud = int(bcb.currentText() or "9600") if bcb else 9600
        except ValueError:
            baud = 9600

        ok, err = False, None
        try:
            # 1. 서비스의 connect 메서드 호출
            ok = self.loadcell_service.connect(port_text, baud, parity='E')
        except Exception as e:
            err = e
            ok = False

        logger.info(f"[LC] Connect → {port_text} @ {baud} : {ok}")


        if ok:
            # 2. 연결 성공 시, 모니터 생성 및 주입
            if not self.lc_monitor:
                serial_obj = self.loadcell_service.get_serial_object()
                
                self.lc_monitor = LoadcellMonitor(
                    serial_obj, 
                    self.data_handler.update_loadcell_value, 
                    self.monitor_interval_ms
                )

            if hasattr(self.ui, "progressBar_2"): self.ui.progressBar_2.setValue(100)
            QtWidgets.QMessageBox.information(self, "연결 성공",
                                              f"로드셀 연결 성공: {port_text} @ {baud}")
            if hasattr(self.ui, "Comdisconnect_pushButton_2"):
                self.ui.Comdisconnect_pushButton_2.setEnabled(True)
            if hasattr(self.ui, "Comconnect_pushButton_2"):
                self.ui.Comconnect_pushButton_2.setEnabled(False)
        else:
            logger.error(f"로드셀 연결 실패: {port_text} @ {baud}\n{err or ''}")
            if hasattr(self.ui, "progressBar_2"): self.ui.progressBar_2.setValue(0)
            QtWidgets.QMessageBox.warning(self, "연결 실패",
                                          f"로드셀 연결 실패: {port_text} @ {baud}\n{err or ''}")
            if hasattr(self.ui, "Comconnect_pushButton_2"):
                self.ui.Comconnect_pushButton_2.setEnabled(True)
            if hasattr(self.ui, "Comdisconnect_pushButton_2"):
                self.ui.Comdisconnect_pushButton_2.setEnabled(False)

    def on_com_disconnect_lc(self):
        # 1) 중앙 정지 함수 호출 (테스트, 플로팅 등 모두 중지)
        self._stop_all_tests(reason="로드셀 연결 해제")

        # 2) 모니터 타이머 먼저 정지
        if self.lc_monitor:
            try:
                self.lc_monitor.stop()   # QTimer 중지 → 값 요청 중단
            except Exception as e:
                logger.error(f"[LC] monitor.stop() 예외: {e}")
            self.lc_monitor = None

        # 3) 서비스의 disconnect 메서드 호출
        try:
            self.loadcell_service.disconnect() # <- 서비스 메서드 호출
        except Exception as e:
            logger.error(f"disconnect 예외: {e}")

        # 4) UI 정리 (DataHandler에 위임)
        self.data_handler.reset_ui_labels()
            
        if hasattr(self.ui, "progressBar_2"):
            self.ui.progressBar_2.setValue(0)

        # 가드 플래그 리셋 (DataHandler에 위임)
        self.data_handler.reset_force_guard()

        logger.info("로드셀 연결을 해제했습니다.")
        QtWidgets.QMessageBox.information(self, "연결 해제", "로드셀 연결을 해제했습니다.")

        if hasattr(self.ui, "Comconnect_pushButton_2"):
            self.ui.Comconnect_pushButton_2.setEnabled(True)
        if hasattr(self.ui, "Comdisconnect_pushButton_2"):
            self.ui.Comdisconnect_pushButton_2.setEnabled(False)

    # =========================================================
    #  Temp Controller Connect / Disconnect
    # =========================================================
    def on_com_connect_temp(self):
        """온도 제어기 연결 및 매니저 서비스 시작"""
        # 1. 포트 및 보드레이트 정보 가져오기
        c3 = getattr(self.ui, "Com_comboBox_3", QtWidgets.QComboBox())
        port_text = (c3.currentText() or "").strip()
        
        if not port_text:
            self.refresh_com_ports()
            QtWidgets.QMessageBox.information(self, "포트 선택 필요", "포트를 선택하거나 장치를 연결하세요.")
            return

        try:
            baud_cb = getattr(self.ui, "Baud_comboBox_3", None)
            baud = int(baud_cb.currentText() or "9600") if baud_cb else 9600
        except ValueError:
            baud = 9600

        # 2. Modbus 클라이언트 객체 생성
        from pymodbus.client.serial import ModbusSerialClient
        self.temp_client = ModbusSerialClient(
            port=port_text, 
            baudrate=baud, 
            bytesize=8, 
            parity='N', 
            stopbits=1, 
            timeout=1.0
        )

        ok, err = False, None

        try:
            # 3. 물리적 연결 시도
            if self.temp_client.connect():
                logger.info(f"[TEMP] 연결 시도 중... (Port: {port_text})")
                
                # Handshake: CH1의 PV(현재온도) 주소인 0x03E8을 읽어 통신 확인
                chk = self.temp_client.read_input_registers(address=0x0066, count=1)
                
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
                err = "포트를 열 수 없습니다. (다른 프로그램에서 사용 중인지 확인하세요)"

        except Exception as e:
            ok = False
            err = str(e)
            if self.temp_client:
                self.temp_client.close()

        # 4. 최종 연결 결과 처리
        if ok:
            # --- 계층 구조에 따른 서비스 시작 ---
            if hasattr(self, 'temp_manager'):
                # Manager_temp를 통해 컨트롤러/모니터링 스레드 일괄 시작
                self.temp_manager.start_service(self.temp_client, 1000) # 1000ms 주기
            
            logger.info(f"[TEMP] 연결 성공: {port_text}")
            QtWidgets.QMessageBox.information(self, "연결 성공", f"온도 제어기 연결 성공: {port_text}")
            
            if hasattr(self.ui, "Comdisconnect_pushButton_3"):
                self.ui.Comdisconnect_pushButton_3.setEnabled(True)
            if hasattr(self.ui, "Comconnect_pushButton_3"):
                self.ui.Comconnect_pushButton_3.setEnabled(False)
        else:
            logger.error(f"[TEMP] 연결 실패: {err}")
            QtWidgets.QMessageBox.warning(self, "연결 실패", f"온도 제어기 연결 실패:\n{err}")
            self.temp_client = None

    def on_com_disconnect_temp(self):
        # 1. 클라이언트 연결 해제
        try:
            if self.temp_client:
                self.temp_client.close()
        except Exception as e:
                logger.error(f"[TEMP] close 예외: {e}")
        
        # 2. 클라이언트 객체 해제
        self.temp_manager.stop_service()

        logger.info("온도 제어기 연결을 해제했습니다.")
        QtWidgets.QMessageBox.information(self, "연결 해제", "온도 제어기 연결을 해제했습니다.")
        if hasattr(self.ui, "Comconnect_pushButton_3"):
            self.ui.Comconnect_pushButton_3.setEnabled(True)
        if hasattr(self.ui, "Comdisconnect_pushButton_3"):
            self.ui.Comdisconnect_pushButton_3.setEnabled(False)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    app.setStyle("Fusion")
    
    # ========== 글로벌 폰트 설정 ==========
    try:
        app_font = QtGui.QFont("Pretendard", 10, QtGui.QFont.DemiBold)
    except Exception:
        app_font = QtGui.QFont("Arial", 10, QtGui.QFont.Bold)
    app.setFont(app_font)
    # ============================================
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())