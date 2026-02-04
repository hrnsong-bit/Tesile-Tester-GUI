from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import PlotWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1280, 844)
        MainWindow.setAutoFillBackground(True)
        MainWindow.setDocumentMode(False)
        MainWindow.setDockNestingEnabled(False)
        MainWindow.setUnifiedTitleAndToolBarOnMac(False)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        # 메인 레이아웃
        main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 메인 탭 위젯
        self.Main_tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.Main_tabWidget.setObjectName("Main_tabWidget")

        # ===== 탭 바 오른쪽 코너에 메뉴 배치 =====
        # 메뉴 컨테이너 위젯
        menu_widget = QtWidgets.QWidget()
        menu_layout = QtWidgets.QHBoxLayout(menu_widget)
        menu_layout.setContentsMargins(0, 0, 10, 0)
        menu_layout.setSpacing(15)

        # Font 메뉴 버튼
        self.font_menu_btn = QtWidgets.QPushButton("Font")
        self.font_menu_btn.setFlat(True)
        self.font_menu_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.font_menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #0066cc;
                font-size: 10pt;
                padding: 3px 8px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #0052a3;
                background-color: rgba(0, 102, 204, 0.08);
                border-radius: 3px;
            }
        """)
        menu_layout.addWidget(self.font_menu_btn)

        # 구분선
        separator1 = QtWidgets.QLabel("|")
        separator1.setStyleSheet("color: #cccccc; font-size: 10pt;")
        menu_layout.addWidget(separator1)

        # ===== 언어 전환 버튼 추가 =====
        self.language_toggle_btn = QtWidgets.QPushButton("EN")
        self.language_toggle_btn.setFlat(True)
        self.language_toggle_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.language_toggle_btn.setFixedSize(35, 25)  # 작은 버튼 크기
        self.language_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                border: none;
                color: white;
                font-size: 9pt;
                font-weight: bold;
                padding: 2px 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
            QPushButton:pressed {
                background-color: #003d7a;
            }
        """)
        menu_layout.addWidget(self.language_toggle_btn)

        # 구분선
        separator2 = QtWidgets.QLabel("|")
        separator2.setStyleSheet("color: #cccccc; font-size: 10pt;")
        menu_layout.addWidget(separator2)

        # About 메뉴 버튼
        self.about_menu_btn = QtWidgets.QPushButton("About")
        self.about_menu_btn.setFlat(True)
        self.about_menu_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.about_menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #0066cc;
                font-size: 10pt;
                padding: 3px 8px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #0052a3;
                background-color: rgba(0, 102, 204, 0.08);
                border-radius: 3px;
            }
        """)
        menu_layout.addWidget(self.about_menu_btn)

        # 탭 위젯의 오른쪽 코너에 메뉴 위젯 배치
        self.Main_tabWidget.setCornerWidget(menu_widget, QtCore.Qt.TopRightCorner)

        # 메인 레이아웃에 탭 위젯 추가
        main_layout.addWidget(self.Main_tabWidget)
                
        # =================================================================
        # 1. COM Set 탭 (tab_2)
        # =================================================================
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        
        com_main_layout = QtWidgets.QVBoxLayout(self.tab_2)
        com_main_layout.setContentsMargins(20, 20, 20, 20)
        com_main_layout.setSpacing(20)
        
        com_main_layout.addStretch(1)
        
        # COM 포트 그룹박스들을 담을 가로 레이아웃
        com_boxes_layout = QtWidgets.QHBoxLayout()
        com_boxes_layout.setSpacing(20)
        
        com_boxes_layout.addStretch(1)
        
        # -------------------------------------------------------
        # [1] Motor COM GroupBox
        # -------------------------------------------------------
        self.COM_groupBox = self._create_com_groupbox(
            "Motor",
            "Com_label", "Com_comboBox", "Comrefresh_pushButton",
            "Baud_label", "Baud_comboBox",
            "Comconnect_pushButton", "Comdisconnect_pushButton"
        )
        com_boxes_layout.addWidget(self.COM_groupBox)
        
        # -------------------------------------------------------
        # [2] LoadCell COM GroupBox
        # -------------------------------------------------------
        self.COM_groupBox_2 = self._create_com_groupbox(
            "Load Cell",
            "Com_label_2", "Com_comboBox_2", "Comrefresh_pushButton_2",
            "Baud_label_2", "Baud_comboBox_2",
            "Comconnect_pushButton_2", "Comdisconnect_pushButton_2"
        )
        com_boxes_layout.addWidget(self.COM_groupBox_2)
        
        # -------------------------------------------------------
        # [3] Temp Controller COM GroupBox
        # -------------------------------------------------------
        self.COM_groupBox_3 = self._create_com_groupbox(
            "Temp Controller",
            "Com_label_3", "Com_comboBox_3", "Comrefresh_pushButton_3",
            "Baud_label_3", "Baud_comboBox_3",
            "Comconnect_pushButton_3", "Comdisconnect_pushButton_3"
        )
        com_boxes_layout.addWidget(self.COM_groupBox_3)
        
        com_boxes_layout.addStretch(1)
        
        com_main_layout.addLayout(com_boxes_layout)
        com_main_layout.addStretch(1)
        
        self.Main_tabWidget.addTab(self.tab_2, "")
        
        # =================================================================
        # 2. Setting 탭 (tab)
        # =================================================================
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")

        # 메인 가로 레이아웃
        setting_main_layout = QtWidgets.QHBoxLayout(self.tab)
        setting_main_layout.setContentsMargins(10, 10, 10, 10)
        setting_main_layout.setSpacing(30)

        # ========================================================================
        # 왼쪽 컬럼 (Load0, Encoder0, Monitoring Hz, Safety)
        # ========================================================================
        left_column = QtWidgets.QVBoxLayout()
        left_column.setSpacing(10)

        # 1. Load to 0 Point Set
        self.Load0_groupBox = QtWidgets.QGroupBox("Load to 0 Point Set")
        self.Load0_groupBox.setMinimumSize(QtCore.QSize(400, 100))
        # setMaximumSize 제거 - 가변 크기 허용
        self.Load0_groupBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        load0_layout = QtWidgets.QVBoxLayout(self.Load0_groupBox)
        load0_layout.setContentsMargins(10, 10, 10, 10)
        load0_layout.setSpacing(8)

        load0_value_layout = QtWidgets.QHBoxLayout()
        load0_value_layout.setSpacing(10)
        self.Load0Currentnow_labeltxt = QtWidgets.QLabel("Load Cell Force")
        self.Load0Currentnow_labeltxt.setMinimumWidth(100)
        self.Load0Currentnow_label = QtWidgets.QLabel("")
        self.Load0Currentnow_label.setStyleSheet("""
            background-color: rgb(255,255,255);
            border: 1px solid #CCCCCC;
            padding: 4px;
            font-size: 11pt;
        """)
        self.Load0Currentnow_label.setMinimumHeight(30)
        self.Load0Currentnow_label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        self.Load0_pushButton = QtWidgets.QPushButton("Set")
        self.Load0_pushButton.setMinimumSize(QtCore.QSize(80, 30))
        self.Load0_pushButton.setMaximumWidth(120)
        load0_value_layout.addWidget(self.Load0Currentnow_labeltxt)
        load0_value_layout.addWidget(self.Load0Currentnow_label, 1)
        load0_value_layout.addWidget(self.Load0_pushButton)

        load0_layout.addLayout(load0_value_layout)

        left_column.addWidget(self.Load0_groupBox, 1)  # stretch factor 추가

        # 2. Encoder to 0 Point Set
        self.En0_groupBox = QtWidgets.QGroupBox("Encoder to 0 Point Set")
        self.En0_groupBox.setMinimumSize(QtCore.QSize(400, 100))
        self.En0_groupBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        en0_layout = QtWidgets.QVBoxLayout(self.En0_groupBox)
        en0_layout.setContentsMargins(10, 10, 10, 10)
        en0_layout.setSpacing(8)

        en0_value_layout = QtWidgets.QHBoxLayout()
        en0_value_layout.setSpacing(10)
        self.En0Positionnow_labeltxt = QtWidgets.QLabel("Encoder Position")
        self.En0Positionnow_labeltxt.setMinimumWidth(100)
        self.En0Positionnow_label = QtWidgets.QLabel("")
        self.En0Positionnow_label.setStyleSheet("""
            background-color: rgb(255,255,255);
            border: 1px solid #CCCCCC;
            padding: 4px;
            font-size: 11pt;
        """)
        self.En0Positionnow_label.setMinimumHeight(30)
        self.En0Positionnow_label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        self.En0_pushButton = QtWidgets.QPushButton("Set")
        self.En0_pushButton.setMinimumSize(QtCore.QSize(80, 30))
        self.En0_pushButton.setMaximumWidth(120)
        en0_value_layout.addWidget(self.En0Positionnow_labeltxt)
        en0_value_layout.addWidget(self.En0Positionnow_label, 1)
        en0_value_layout.addWidget(self.En0_pushButton)

        en0_layout.addLayout(en0_value_layout)

        left_column.addWidget(self.En0_groupBox, 1)  # stretch factor 추가

        # 3. Monitoring Frequency
        self.hz_groupBox = QtWidgets.QGroupBox("Monitoring Frequency")
        self.hz_groupBox.setMinimumSize(QtCore.QSize(400, 80))
        self.hz_groupBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        hz_layout = QtWidgets.QHBoxLayout(self.hz_groupBox)
        hz_layout.setContentsMargins(10, 10, 10, 10)
        hz_layout.setSpacing(10)

        # ===== 라벨을 self.hz_label로 저장 =====
        self.hz_label = QtWidgets.QLabel("Set Frequency:")
        self.hz_label.setMinimumWidth(100)

        self.hz_spinBox = QtWidgets.QSpinBox()
        self.hz_spinBox.setSuffix(" Hz")
        self.hz_spinBox.setMinimum(1)
        self.hz_spinBox.setMaximum(100)
        self.hz_spinBox.setValue(10)
        self.hz_spinBox.setMinimumHeight(24)
        self.hz_spinBox.setMaximumHeight(30)
        self.hz_spinBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )

        self.hz_set_pushButton = QtWidgets.QPushButton("Set")
        self.hz_set_pushButton.setMinimumSize(QtCore.QSize(80, 30))
        self.hz_set_pushButton.setMaximumWidth(120)

        hz_layout.addWidget(self.hz_label)  # ← 변경됨
        hz_layout.addWidget(self.hz_spinBox, 1)
        hz_layout.addWidget(self.hz_set_pushButton)

        left_column.addWidget(self.hz_groupBox, 1)

        # 4. Safety Limit
        self.Safty_groupBox = QtWidgets.QGroupBox("Safety Limit")
        self.Safty_groupBox.setMinimumSize(QtCore.QSize(400, 260))
        self.Safty_groupBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding  # 세로로도 확장
        )
        safety_layout = QtWidgets.QVBoxLayout(self.Safty_groupBox)
        safety_layout.setContentsMargins(10, 10, 10, 10)
        safety_layout.setSpacing(8)

        # Displacement Section
        self.Com_label_8 = QtWidgets.QLabel("Displacement (mm)")
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        self.Com_label_8.setFont(font)

        disp_high_layout = QtWidgets.QHBoxLayout()
        disp_high_layout.setSpacing(10)
        self.DisplaceLimitMax_doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.DisplaceLimitMax_doubleSpinBox.setMaximum(999.99)
        self.DisplaceLimitMax_doubleSpinBox.setSingleStep(0.1)
        self.DisplaceLimitMax_doubleSpinBox.setValue(0.20)
        self.DisplaceLimitMax_doubleSpinBox.setMinimumHeight(30)
        self.DisplaceLimitMax_doubleSpinBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        self.Com_label_6 = QtWidgets.QLabel("High")
        self.Com_label_6.setMinimumWidth(50)
        disp_high_layout.addWidget(self.DisplaceLimitMax_doubleSpinBox, 1)
        disp_high_layout.addWidget(self.Com_label_6)

        disp_low_layout = QtWidgets.QHBoxLayout()
        disp_low_layout.setSpacing(10)
        self.DisplaceLimitMin_doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.DisplaceLimitMin_doubleSpinBox.setMaximum(999.99)
        self.DisplaceLimitMin_doubleSpinBox.setSingleStep(0.1)
        self.DisplaceLimitMin_doubleSpinBox.setValue(0.00)
        self.DisplaceLimitMin_doubleSpinBox.setMinimumHeight(30)
        self.DisplaceLimitMin_doubleSpinBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        self.Com_label_12 = QtWidgets.QLabel("Low")
        self.Com_label_12.setMinimumWidth(50)
        disp_low_layout.addWidget(self.DisplaceLimitMin_doubleSpinBox, 1)
        disp_low_layout.addWidget(self.Com_label_12)

        # Separator Line
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

        # Force Section
        self.Com_label_10 = QtWidgets.QLabel("Force (N)")
        self.Com_label_10.setFont(font)

        force_layout = QtWidgets.QHBoxLayout()
        force_layout.setSpacing(10)
        self.ForceLimitMax_doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.ForceLimitMax_doubleSpinBox.setMaximum(999.99)
        self.ForceLimitMax_doubleSpinBox.setSingleStep(0.1)
        self.ForceLimitMax_doubleSpinBox.setValue(0.00)
        self.ForceLimitMax_doubleSpinBox.setMinimumHeight(30)
        self.ForceLimitMax_doubleSpinBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        self.Com_label_13 = QtWidgets.QLabel("Displacement")
        self.Com_label_13.setMinimumWidth(100)
        force_layout.addWidget(self.ForceLimitMax_doubleSpinBox, 1)
        force_layout.addWidget(self.Com_label_13)

        safety_layout.addWidget(self.Com_label_8)
        safety_layout.addLayout(disp_high_layout)
        safety_layout.addLayout(disp_low_layout)
        safety_layout.addSpacing(10)
        safety_layout.addWidget(line)
        safety_layout.addSpacing(10)
        safety_layout.addWidget(self.Com_label_10)
        safety_layout.addLayout(force_layout)
        safety_layout.addStretch(1)  # Safety 내부 여백

        left_column.addWidget(self.Safty_groupBox, 3)  # 더 큰 stretch factor

        # ========================================================================
        # 오른쪽 컬럼 (Motor Speed, Jog Speed, Pre-Tension)
        # ========================================================================
        right_column = QtWidgets.QVBoxLayout()
        right_column.setSpacing(10)

        # 1. Motor Speed Setting
        self.Motspeed_groupBox = QtWidgets.QGroupBox("Motor Speed Setting")
        self.Motspeed_groupBox.setMinimumSize(QtCore.QSize(450, 220))
        self.Motspeed_groupBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding  # 세로로도 확장
        )
        motor_layout = QtWidgets.QVBoxLayout(self.Motspeed_groupBox)
        motor_layout.setContentsMargins(10, 10, 10, 10)
        motor_layout.setSpacing(8)

        # 사용자 지정 입력 + Set Speed 버튼을 한 줄에
        motor_input_layout = QtWidgets.QHBoxLayout()
        motor_input_layout.setSpacing(10)
        self.MotorSpeed_checkBox = QtWidgets.QCheckBox("사용자 지정")
        self.MotorSpeed_checkBox.setMinimumWidth(80)
        self.MotorSpeed_spinBox = QtWidgets.QSpinBox()
        self.MotorSpeed_spinBox.setMaximum(5000)
        self.MotorSpeed_spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.MotorSpeed_spinBox.setMinimumHeight(30)
        self.MotorSpeed_spinBox.setMinimumWidth(80)
        self.MotorSpeed_spinBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        self.MotorSpeedUnit_label = QtWidgets.QLabel("[um/sec]")
        self.MotorSpeedUnit_label.setMinimumWidth(60)
        self.Setmotorspeed_pushButton = QtWidgets.QPushButton("Set Speed")
        self.Setmotorspeed_pushButton.setMinimumSize(QtCore.QSize(100, 30))
        self.Setmotorspeed_pushButton.setMaximumWidth(120)

        motor_input_layout.addWidget(self.MotorSpeed_checkBox)
        motor_input_layout.addWidget(self.MotorSpeed_spinBox, 1)
        motor_input_layout.addWidget(self.MotorSpeedUnit_label)
        motor_input_layout.addWidget(self.Setmotorspeed_pushButton)

        # 프리셋 라디오 버튼
        motor_preset_layout = QtWidgets.QGridLayout()
        motor_preset_layout.setSpacing(8)
        motor_preset_layout.setHorizontalSpacing(30)

        self.Motor10_radioButton = QtWidgets.QRadioButton("10 um")
        self.Motor20_radioButton = QtWidgets.QRadioButton("20 um")
        self.Motor30_radioButton = QtWidgets.QRadioButton("30 um")
        self.Motor40_radioButton = QtWidgets.QRadioButton("40 um")
        self.Motor50_radioButton = QtWidgets.QRadioButton("50 um")
        self.Motor100_radioButton = QtWidgets.QRadioButton("100 um")
        self.Motor200_radioButton = QtWidgets.QRadioButton("200 um")
        self.Motor300_radioButton = QtWidgets.QRadioButton("300 um")

        motor_preset_layout.addWidget(self.Motor10_radioButton, 0, 0)
        motor_preset_layout.addWidget(self.Motor20_radioButton, 1, 0)
        motor_preset_layout.addWidget(self.Motor30_radioButton, 2, 0)
        motor_preset_layout.addWidget(self.Motor40_radioButton, 3, 0)
        motor_preset_layout.addWidget(self.Motor50_radioButton, 0, 1)
        motor_preset_layout.addWidget(self.Motor100_radioButton, 1, 1)
        motor_preset_layout.addWidget(self.Motor200_radioButton, 2, 1)
        motor_preset_layout.addWidget(self.Motor300_radioButton, 3, 1)

        motor_layout.addLayout(motor_input_layout)
        motor_layout.addLayout(motor_preset_layout)
        motor_layout.addStretch(1)  # 내부 여백

        right_column.addWidget(self.Motspeed_groupBox, 2)  # stretch factor

        # 2. Jog Speed Setting
        self.groupBox_9 = QtWidgets.QGroupBox("Jog Speed Setting")
        self.groupBox_9.setMinimumSize(QtCore.QSize(450, 280))
        self.groupBox_9.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding  # 세로로도 확장
        )
        jog_main_layout = QtWidgets.QVBoxLayout(self.groupBox_9)
        jog_main_layout.setContentsMargins(10, 10, 10, 10)
        jog_main_layout.setSpacing(8)

        # Jog 속도 설정 부분
        jog_speed_widget = QtWidgets.QWidget()
        jog_layout = QtWidgets.QVBoxLayout(jog_speed_widget)
        jog_layout.setContentsMargins(0, 0, 0, 0)
        jog_layout.setSpacing(8)

        # 사용자 지정 입력 + Set Speed 버튼을 한 줄에
        jog_input_layout = QtWidgets.QHBoxLayout()
        jog_input_layout.setSpacing(10)
        self.Jog_checkBox = QtWidgets.QCheckBox("사용자 지정")
        self.Jog_checkBox.setMinimumWidth(80)
        self.Jog_spinBox = QtWidgets.QSpinBox()
        self.Jog_spinBox.setMaximum(5000)
        self.Jog_spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.Jog_spinBox.setMinimumHeight(30)
        self.Jog_spinBox.setMinimumWidth(80)
        self.Jog_spinBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        self.Com_label_15 = QtWidgets.QLabel("[um/sec]")
        self.Com_label_15.setMinimumWidth(60)
        self.Setjogspeed_pushButton = QtWidgets.QPushButton("Set Speed")
        self.Setjogspeed_pushButton.setMinimumSize(QtCore.QSize(100, 30))
        self.Setjogspeed_pushButton.setMaximumWidth(120)

        jog_input_layout.addWidget(self.Jog_checkBox)
        jog_input_layout.addWidget(self.Jog_spinBox, 1)
        jog_input_layout.addWidget(self.Com_label_15)
        jog_input_layout.addWidget(self.Setjogspeed_pushButton)

        jog_preset_layout = QtWidgets.QGridLayout()
        jog_preset_layout.setSpacing(8)
        jog_preset_layout.setHorizontalSpacing(30)

        self.jog10_radioButton = QtWidgets.QRadioButton("10 um")
        self.jog20_radioButton = QtWidgets.QRadioButton("20 um")
        self.jog30_radioButton = QtWidgets.QRadioButton("30 um")
        self.jog40_radioButton = QtWidgets.QRadioButton("40 um")
        self.jog50_radioButton = QtWidgets.QRadioButton("50 um")
        self.jog100_radioButton = QtWidgets.QRadioButton("100 um")
        self.jog200_radioButton = QtWidgets.QRadioButton("200 um")
        self.jog500_radioButton = QtWidgets.QRadioButton("500 um")

        jog_preset_layout.addWidget(self.jog10_radioButton, 0, 0)
        jog_preset_layout.addWidget(self.jog20_radioButton, 1, 0)
        jog_preset_layout.addWidget(self.jog30_radioButton, 2, 0)
        jog_preset_layout.addWidget(self.jog40_radioButton, 3, 0)
        jog_preset_layout.addWidget(self.jog50_radioButton, 0, 1)
        jog_preset_layout.addWidget(self.jog100_radioButton, 1, 1)
        jog_preset_layout.addWidget(self.jog200_radioButton, 2, 1)
        jog_preset_layout.addWidget(self.jog500_radioButton, 3, 1)

        jog_layout.addLayout(jog_input_layout)
        jog_layout.addLayout(jog_preset_layout)
        jog_layout.addStretch(1)  # 내부 여백

        # Jog 제어 버튼
        self.groupBox_10 = QtWidgets.QGroupBox("Jog Control")
        self.groupBox_10.setMinimumHeight(70)
        self.groupBox_10.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        jog_control_layout = QtWidgets.QHBoxLayout(self.groupBox_10)
        jog_control_layout.setContentsMargins(10, 10, 10, 10)
        jog_control_layout.setSpacing(15)

        self.Jogfowerd_pushButton = QtWidgets.QPushButton("Compression")
        self.Jogfowerd_pushButton.setMinimumSize(QtCore.QSize(100, 35))
        self.Jogfowerd_pushButton.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )

        self.Jogbackwerd_pushButton = QtWidgets.QPushButton("Tensile")
        self.Jogbackwerd_pushButton.setMinimumSize(QtCore.QSize(100, 35))
        self.Jogbackwerd_pushButton.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )

        jog_control_layout.addStretch()
        jog_control_layout.addWidget(self.Jogfowerd_pushButton, 1)
        jog_control_layout.addWidget(self.Jogbackwerd_pushButton, 1)
        jog_control_layout.addStretch()

        jog_main_layout.addWidget(jog_speed_widget, 1)
        jog_main_layout.addWidget(self.groupBox_10)

        right_column.addWidget(self.groupBox_9, 3)  # stretch factor

        # 3. Pre-Tension
        self.tension_groupBox = QtWidgets.QGroupBox("Pre-Tension")
        self.tension_groupBox.setMinimumSize(QtCore.QSize(450, 150))
        self.tension_groupBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        tension_layout = QtWidgets.QFormLayout(self.tension_groupBox)
        tension_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        tension_layout.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        tension_layout.setVerticalSpacing(10)
        tension_layout.setContentsMargins(10, 10, 10, 10)

        self.tension_speed_label = QtWidgets.QLabel("조정 속도:") 
        self.tension_speed_spinBox = QtWidgets.QDoubleSpinBox()
        self.tension_speed_spinBox.setSuffix(" um/sec")
        self.tension_speed_spinBox.setMinimum(10)
        self.tension_speed_spinBox.setMaximum(1000.0)
        self.tension_speed_spinBox.setValue(10.0)
        self.tension_speed_spinBox.setSingleStep(10.0)
        self.tension_speed_spinBox.setMinimumHeight(30)
        self.tension_speed_spinBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        tension_layout.addRow(self.tension_speed_label, self.tension_speed_spinBox)

        self.tension_force_label = QtWidgets.QLabel("감지 하중:") 
        self.tension_force_spinBox = QtWidgets.QDoubleSpinBox()
        self.tension_force_spinBox.setSuffix(" N")
        self.tension_force_spinBox.setMinimum(-999)
        self.tension_force_spinBox.setMaximum(999)
        self.tension_force_spinBox.setValue(0.1)
        self.tension_force_spinBox.setDecimals(3)
        self.tension_force_spinBox.setSingleStep(0.1)
        self.tension_force_spinBox.setMinimumHeight(30)
        self.tension_force_spinBox.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        tension_layout.addRow(self.tension_force_label, self.tension_force_spinBox)
        
        tension_button_layout = QtWidgets.QHBoxLayout()
        tension_button_layout.setSpacing(10)

        self.tension_start_pushButton = QtWidgets.QPushButton("조정 시작")
        self.tension_start_pushButton.setMinimumSize(QtCore.QSize(100, 30))
        self.tension_start_pushButton.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        tension_button_layout.addWidget(self.tension_start_pushButton, 1)

        self.tension_stop_pushButton = QtWidgets.QPushButton("수동 정지")
        self.tension_stop_pushButton.setMinimumSize(QtCore.QSize(100, 30))
        self.tension_stop_pushButton.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred
        )
        tension_button_layout.addWidget(self.tension_stop_pushButton, 1)

        tension_layout.addRow(tension_button_layout)

        right_column.addWidget(self.tension_groupBox, 2)  # stretch factor

        # 메인 레이아웃에 좌우 컬럼 추가 (가로로도 동일 비율 확장)
        setting_main_layout.addLayout(left_column, 1)
        setting_main_layout.addLayout(right_column, 1)

        self.Main_tabWidget.addTab(self.tab, "")

        # =================================================================
        # 3. Temp 탭
        # =================================================================
        self.tab_new = QtWidgets.QWidget()
        self.tab_new.setObjectName("Temp")
        
        # 메인 가로 레이아웃
        self.temp_main_layout = QtWidgets.QHBoxLayout(self.tab_new)
        self.temp_main_layout.setContentsMargins(10, 10, 10, 10)
        self.temp_main_layout.setSpacing(15)

        # 왼쪽 채널 컨트롤 패널
        self.temp_ctrl_group = QtWidgets.QGroupBox("Channel Monitor & Control")
        self.temp_ctrl_group.setMinimumWidth(320)
        self.temp_ctrl_group.setMaximumWidth(400)
        self.ctrl_vbox = QtWidgets.QVBoxLayout(self.temp_ctrl_group)
        
        # 채널별 위젯 참조 딕셔너리
        self.temp_channels = {}
        colors = ['#EA002C', '#00A0E9', '#9BCF0A', '#F47725']

        for i in range(1, 5):
            channel_row = QtWidgets.QHBoxLayout()
            
            chk = QtWidgets.QCheckBox(f"CH {i} Display")
            chk.setChecked(True)
            chk.setStyleSheet(f"color: {colors[i-1]}; font-weight: bold; font-size: 11pt;")
            
            lbl = QtWidgets.QLabel("0.0 °C")
            lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            lbl.setMinimumSize(QtCore.QSize(100, 35))
            lbl.setStyleSheet("""
                font-size: 16pt; 
                font-family: 'Consolas'; 
                background-color: #F8F8F8; 
                border: 1px solid #CCCCCC; 
                padding-right: 5px;
                border-radius: 4px;
            """)
            
            channel_row.addWidget(chk)
            channel_row.addWidget(lbl, 1)
            self.ctrl_vbox.addLayout(channel_row)
            
            self.temp_channels[i] = {"chk": chk, "lbl": lbl, "color": colors[i-1]}

        self.ctrl_vbox.addSpacing(15)

        # 구분선
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.ctrl_vbox.addWidget(line)
        self.ctrl_vbox.addSpacing(10)

        # CH1 제어 설정
        self.temp_setting_group = QtWidgets.QGroupBox("Control Settings")
        self.temp_setting_form = QtWidgets.QFormLayout(self.temp_setting_group)
        self.temp_setting_form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.temp_setting_form.setVerticalSpacing(10)

        # CH1 SV 입력
        self.temp_sv_label = QtWidgets.QLabel("CH1 Target:")
        self.temp_sv_input = QtWidgets.QDoubleSpinBox()
        self.temp_sv_input.setRange(0, 500)
        self.temp_sv_input.setDecimals(1)
        self.temp_sv_input.setSuffix(" °C")
        self.temp_sv_input.setMinimumHeight(35)
        self.temp_setting_form.addRow(self.temp_sv_label, self.temp_sv_input)

        # 오토튜닝 ON/OFF
        self.at_exec_label = QtWidgets.QLabel("Auto Tuning:") 
        self.at_exec_combo = QtWidgets.QComboBox()
        self.at_exec_combo.addItems(["OFF (정지)", "ON (실행)"])
        self.at_exec_combo.setMinimumHeight(35)
        self.at_exec_combo.setCurrentIndex(1)
        self.temp_setting_form.addRow(self.at_exec_label, self.at_exec_combo)

        # 구분선
        line_stabilization = QtWidgets.QFrame()
        line_stabilization.setFrameShape(QtWidgets.QFrame.HLine)
        line_stabilization.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.temp_setting_form.addRow(line_stabilization)

        # 안정화 범위 설정
        self.temp_stability_range_label = QtWidgets.QLabel("Stability Range (±):") 
        self.temp_stability_range = QtWidgets.QDoubleSpinBox()
        self.temp_stability_range.setRange(0.1, 50.0)
        self.temp_stability_range.setDecimals(1)
        self.temp_stability_range.setSuffix(" °C")
        self.temp_stability_range.setValue(2.0)
        self.temp_stability_range.setMinimumHeight(35)
        self.temp_setting_form.addRow(self.temp_stability_range_label, self.temp_stability_range)

        # 안정화 시간 설정
        self.temp_stability_time_label = QtWidgets.QLabel("Stability Time:")
        self.temp_stability_time = QtWidgets.QSpinBox()
        self.temp_stability_time.setRange(1, 60)
        self.temp_stability_time.setSuffix(" min")
        self.temp_stability_time.setValue(5)
        self.temp_stability_time.setMinimumHeight(35)
        self.temp_setting_form.addRow(self.temp_stability_time_label, self.temp_stability_time)

        # 안정화 감지 활성화
        self.temp_stability_enabled = QtWidgets.QCheckBox("Enable Stability Detection")
        self.temp_stability_enabled.setChecked(True)
        self.temp_stability_enabled.setMinimumHeight(35)
        self.temp_setting_form.addRow(self.temp_stability_enabled)

        self.ctrl_vbox.addWidget(self.temp_setting_group)
        
        # 그래프 뷰 모드 선택
        self.temp_view_group = QtWidgets.QGroupBox("Graph View Mode")
        self.temp_view_layout = QtWidgets.QVBoxLayout(self.temp_view_group)

        self.temp_view_unified = QtWidgets.QRadioButton("Unified View (4 channels)")
        self.temp_view_unified.setChecked(True)
        self.temp_view_layout.addWidget(self.temp_view_unified)

        self.temp_view_split = QtWidgets.QRadioButton("Split View (4 graphs)")
        self.temp_view_layout.addWidget(self.temp_view_split)

        self.ctrl_vbox.addWidget(self.temp_view_group)
        
        # ===== 자동 범위 체크박스 =====
        self.temp_auto_range_checkbox = QtWidgets.QCheckBox("Auto Scale (uncheck for manual zoom/pan)")
        self.temp_auto_range_checkbox.setChecked(True)
        self.temp_auto_range_checkbox.setToolTip(
            "Check: Auto-scroll to show recent 60 seconds\n"
            "Uncheck: Free zoom/pan with mouse\n"
            "Right-click graph → 'View All' to see all data"
        )
        self.ctrl_vbox.addWidget(self.temp_auto_range_checkbox)
        
        self.ctrl_vbox.addStretch()

        # Start/Stop 버튼
        self.temp_btn_layout = QtWidgets.QHBoxLayout()
        self.temp_btn_layout.setSpacing(5)
        
        self.temp_start_btn = QtWidgets.QPushButton("Start")
        self.temp_start_btn.setMinimumHeight(50)
        self.temp_start_btn.setStyleSheet("""
            color: white; 
            background-color: #4CAF50;
            font-weight: bold; 
            font-size: 12pt;
            border-radius: 5px;
            border: 1px solid #45a049;
        """)
        self.temp_btn_layout.addWidget(self.temp_start_btn)
        
        self.temp_stop_btn = QtWidgets.QPushButton("Stop")
        self.temp_stop_btn.setMinimumHeight(50)
        self.temp_stop_btn.setStyleSheet("""
            color: white; 
            background-color: #f44336;
            font-weight: bold; 
            font-size: 12pt;
            border-radius: 5px;
            border: 1px solid #da190b;
        """)
        self.temp_btn_layout.addWidget(self.temp_stop_btn)
        
        self.ctrl_vbox.addLayout(self.temp_btn_layout)
        
        self.temp_main_layout.addWidget(self.temp_ctrl_group)

        # 오른쪽 실시간 그래프
        self.temp_plot_stack = QtWidgets.QStackedWidget()

        # 통합 뷰
        self.temp_plot = PlotWidget()
        self.temp_plot.setBackground('w')
        self.temp_plot.showGrid(x=True, y=True)
        self.temp_plot.addLegend()
        self.temp_plot.setLabel('left', 'Temperature', units='°C')
        self.temp_plot.setLabel('bottom', 'Time', units='s')

        # 분할 뷰
        self.temp_plot_split_widget = QtWidgets.QWidget()
        self.temp_plot_split_layout = QtWidgets.QGridLayout(self.temp_plot_split_widget)
        self.temp_plot_split_layout.setSpacing(5)

        self.temp_plot_splits = []
        for i in range(4):
            plot = PlotWidget()
            plot.setBackground('w')
            plot.showGrid(x=True, y=True)
            plot.setLabel('left', 'Temperature', units='°C')
            plot.setLabel('bottom', 'Time', units='s')
            plot.setTitle(f'CH{i+1}', color=colors[i], size='12pt')
    
            row = i // 2
            col = i % 2
            self.temp_plot_split_layout.addWidget(plot, row, col)
            self.temp_plot_splits.append(plot)

        self.temp_plot_stack.addWidget(self.temp_plot)
        self.temp_plot_stack.addWidget(self.temp_plot_split_widget)

        self.temp_main_layout.addWidget(self.temp_plot_stack, 1)

        self.Main_tabWidget.addTab(self.tab_new, "")
        
        # =================================================================
        # 4. Test 탭
        # =================================================================
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        
        test_main_layout = QtWidgets.QVBoxLayout(self.tab_3)
        test_main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.tabWidget = QtWidgets.QTabWidget()
        
        # Basic Tensile Test
        self.tab_4 = QtWidgets.QWidget()
        basic_layout = QtWidgets.QVBoxLayout(self.tab_4)
        basic_layout.setContentsMargins(10, 10, 10, 10)
        
        # 설명 텍스트
        self.textEdit = QtWidgets.QTextEdit()
        self.textEdit.setReadOnly(True)
        self.textEdit.setMaximumHeight(80)
        basic_layout.addWidget(self.textEdit)
        
        # 그래프와 정보를 담을 가로 레이아웃
        test_content_layout = QtWidgets.QHBoxLayout()
        
        # 그래프
        self.graphicsView = PlotWidget()
        test_content_layout.addWidget(self.graphicsView, 2)
        
        # 오른쪽 정보 패널
        right_panel = QtWidgets.QWidget()
        right_panel.setMaximumWidth(350)
        right_panel_layout = QtWidgets.QVBoxLayout(right_panel)
        
        # 현재 값 표시
        self.testValuesWidget = QtWidgets.QGroupBox("Current Values")
        self.formLayout = QtWidgets.QFormLayout(self.testValuesWidget)
        
        self.static_load_label = QtWidgets.QLabel("현재 하중 (N):")
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.static_load_label.setFont(font)
        
        self.test_load_label = QtWidgets.QLabel("0.000")
        self.test_load_label.setFont(font)
        self.test_load_label.setStyleSheet("background-color: rgb(255,255,255); border: 1px solid black; padding: 5px;")
        self.test_load_label.setMinimumHeight(35)
        
        self.formLayout.addRow(self.static_load_label, self.test_load_label)

        self.static_pos_label = QtWidgets.QLabel("현재 변위 (um):")
        self.static_pos_label.setFont(font)
        
        self.test_pos_label = QtWidgets.QLabel("0.0")
        self.test_pos_label.setFont(font)
        self.test_pos_label.setStyleSheet("background-color: rgb(255,255,255); border: 1px solid black; padding: 5px;")
        self.test_pos_label.setMinimumHeight(35)
        
        self.formLayout.addRow(self.static_pos_label, self.test_pos_label)
        
        right_panel_layout.addWidget(self.testValuesWidget)
        right_panel_layout.addStretch()
        
        # 제어 버튼
        button_widget = QtWidgets.QWidget()
        button_layout = QtWidgets.QVBoxLayout(button_widget)
        
        start_stop_layout = QtWidgets.QHBoxLayout()
        self.Basicteststart_pushButton = QtWidgets.QPushButton("Start")
        self.Basicteststart_pushButton.setMinimumSize(QtCore.QSize(100, 40))
        start_stop_layout.addWidget(self.Basicteststart_pushButton)
        
        self.Basicteststop_pushButton = QtWidgets.QPushButton("Stop")
        self.Basicteststop_pushButton.setMinimumSize(QtCore.QSize(100, 40))
        start_stop_layout.addWidget(self.Basicteststop_pushButton)
        
        button_layout.addLayout(start_stop_layout)
        
        reset_layout = QtWidgets.QHBoxLayout()
        reset_layout.addStretch()
        self.Basictestreset_pushButton = QtWidgets.QPushButton("Reset")
        self.Basictestreset_pushButton.setMinimumSize(QtCore.QSize(100, 40))
        reset_layout.addWidget(self.Basictestreset_pushButton)
        reset_layout.addStretch()
        
        button_layout.addLayout(reset_layout)
        
        right_panel_layout.addWidget(button_widget)
        
        test_content_layout.addWidget(right_panel)
        
        basic_layout.addLayout(test_content_layout)
        
        self.tabWidget.addTab(self.tab_4, "")
        
        # Torque Test
        self.tab_5 = QtWidgets.QWidget()
        torque_layout = QtWidgets.QVBoxLayout(self.tab_5)
        
        self.textEdit_2 = QtWidgets.QTextEdit()
        self.textEdit_2.setReadOnly(True)
        self.textEdit_2.setMaximumHeight(80)
        torque_layout.addWidget(self.textEdit_2)
        
        torque_layout.addStretch()
        
        torque_control = QtWidgets.QWidget()
        torque_control_layout = QtWidgets.QVBoxLayout(torque_control)
        
        torque_input_layout = QtWidgets.QHBoxLayout()
        self.Com_label_11 = QtWidgets.QLabel("Torque [N]")
        self.torq_set_doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.torq_set_doubleSpinBox.setMaximum(999.99)
        self.torq_set_doubleSpinBox.setMinimumHeight(35)
        torque_input_layout.addWidget(self.Com_label_11)
        torque_input_layout.addWidget(self.torq_set_doubleSpinBox)
        
        torque_button_layout = QtWidgets.QHBoxLayout()
        self.Torqueteststart_pushButton = QtWidgets.QPushButton("Start")
        self.Torqueteststart_pushButton.setMinimumSize(QtCore.QSize(100, 40))
        torque_button_layout.addWidget(self.Torqueteststart_pushButton)
        
        self.Torqueteststop_pushButton = QtWidgets.QPushButton("Stop")
        self.Torqueteststop_pushButton.setMinimumSize(QtCore.QSize(100, 40))
        torque_button_layout.addWidget(self.Torqueteststop_pushButton)
        
        torque_control_layout.addLayout(torque_input_layout)
        torque_control_layout.addLayout(torque_button_layout)
        
        torque_layout.addWidget(torque_control)
        torque_layout.addStretch()
        
        self.tabWidget.addTab(self.tab_5, "")
        
        # Repeat Test
        self.tab_6 = QtWidgets.QWidget()
        self.tabWidget.addTab(self.tab_6, "")
        
        test_main_layout.addWidget(self.tabWidget)
        
        self.Main_tabWidget.addTab(self.tab_3, "")
        
        # =================================================================
        # 5. Data 탭
        # =================================================================
        self.tab_data = QtWidgets.QWidget()
        self.data_tab_layout = QtWidgets.QVBoxLayout(self.tab_data)
        placeholder_label = QtWidgets.QLabel("데이터 탭 콘텐츠가 여기에 표시됩니다.")
        placeholder_label.setAlignment(QtCore.Qt.AlignCenter)
        self.data_tab_layout.addWidget(placeholder_label)
        self.Main_tabWidget.addTab(self.tab_data, "")
        
        MainWindow.setCentralWidget(self.centralwidget)
        
        # 메뉴바와 상태바
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1280, 26))
        MainWindow.setMenuBar(self.menubar)
        
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.Main_tabWidget.setCurrentIndex(0)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
    
    def set_language_manager(self, lang_mgr):
        """언어 관리자 설정"""
        self.lang_mgr = lang_mgr

    def _create_com_groupbox(self, title, *widget_names):
        """COM 포트 GroupBox 생성 헬퍼 메서드"""
        groupbox = QtWidgets.QGroupBox(title)
        groupbox.setMinimumSize(QtCore.QSize(350, 350))
        groupbox.setMaximumSize(QtCore.QSize(400, 400))
        
        main_layout = QtWidgets.QVBoxLayout(groupbox)
        main_layout.setSpacing(15)
        main_layout.addStretch(1)
        
        # COM Port 선택
        com_layout = QtWidgets.QHBoxLayout()
        com_label = QtWidgets.QLabel("COM port")
        setattr(self, widget_names[0], com_label)
        
        com_combo = QtWidgets.QComboBox()
        com_combo.setMinimumSize(QtCore.QSize(100, 25))
        setattr(self, widget_names[1], com_combo)
        
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.setMinimumSize(QtCore.QSize(80, 25))
        setattr(self, widget_names[2], refresh_btn)
        
        com_layout.addStretch()
        com_layout.addWidget(com_label)
        com_layout.addWidget(com_combo)
        com_layout.addWidget(refresh_btn)
        com_layout.addStretch()
        
        main_layout.addLayout(com_layout)
        
        # Baud Rate
        baud_layout = QtWidgets.QHBoxLayout()
        baud_label = QtWidgets.QLabel("Baud-rate")
        setattr(self, widget_names[3], baud_label)
        
        baud_combo = QtWidgets.QComboBox()
        baud_combo.setMinimumSize(QtCore.QSize(100, 25))
        setattr(self, widget_names[4], baud_combo)
        
        baud_layout.addStretch()
        baud_layout.addWidget(baud_label)
        baud_layout.addWidget(baud_combo)
        baud_layout.addStretch()
        
        main_layout.addLayout(baud_layout)
        main_layout.addSpacing(20)
        
        # Connect/Disconnect 버튼
        button_layout = QtWidgets.QHBoxLayout()
        
        connect_btn = QtWidgets.QPushButton("Connect")
        connect_btn.setMinimumSize(QtCore.QSize(100, 35))
        setattr(self, widget_names[5], connect_btn)
        
        disconnect_btn = QtWidgets.QPushButton("Disconnect")
        disconnect_btn.setMinimumSize(QtCore.QSize(100, 35))
        setattr(self, widget_names[6], disconnect_btn)
        
        button_layout.addStretch()
        button_layout.addWidget(connect_btn)
        button_layout.addWidget(disconnect_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        main_layout.addStretch(1)
        
        return groupbox

    def retranslateUi(self, MainWindow, lang_mgr=None):
        """텍스트 번역 적용 (다국어 지원)"""
        _translate = QtCore.QCoreApplication.translate
        
        # 언어 관리자 사용
        if lang_mgr:
            tr = lang_mgr.translate
            
            # ===== 윈도우 타이틀 =====
            MainWindow.setWindowTitle(tr("window.title"))
            
            # ===== 메인 탭 텍스트 =====
            self.Main_tabWidget.setTabText(self.Main_tabWidget.indexOf(self.tab_2), tr("tab.com_set"))
            self.Main_tabWidget.setTabText(self.Main_tabWidget.indexOf(self.tab), tr("tab.setting"))
            self.Main_tabWidget.setTabText(self.Main_tabWidget.indexOf(self.tab_new), tr("tab.temp"))
            self.Main_tabWidget.setTabText(self.Main_tabWidget.indexOf(self.tab_3), tr("tab.test"))
            self.Main_tabWidget.setTabText(self.Main_tabWidget.indexOf(self.tab_data), tr("tab.data"))
            
            # ===== COM Set 탭 =====
            self.COM_groupBox.setTitle(tr("com.motor"))
            self.COM_groupBox_2.setTitle(tr("com.loadcell"))
            self.COM_groupBox_3.setTitle(tr("com.temp"))
            
            # COM 포트 레이블들
            self.Com_label.setText(tr("com.port"))
            self.Com_label_2.setText(tr("com.port"))
            self.Com_label_3.setText(tr("com.port"))
            
            self.Baud_label.setText(tr("com.baudrate"))
            self.Baud_label_2.setText(tr("com.baudrate"))
            self.Baud_label_3.setText(tr("com.baudrate"))
            
            # 버튼들
            self.Comrefresh_pushButton.setText(tr("com.refresh"))
            self.Comrefresh_pushButton_2.setText(tr("com.refresh"))
            self.Comrefresh_pushButton_3.setText(tr("com.refresh"))
            
            self.Comconnect_pushButton.setText(tr("com.connect"))
            self.Comconnect_pushButton_2.setText(tr("com.connect"))
            self.Comconnect_pushButton_3.setText(tr("com.connect"))
            
            self.Comdisconnect_pushButton.setText(tr("com.disconnect"))
            self.Comdisconnect_pushButton_2.setText(tr("com.disconnect"))
            self.Comdisconnect_pushButton_3.setText(tr("com.disconnect"))
            
            # ===== Setting 탭 =====
            # Load to 0 Point Set
            self.Load0_groupBox.setTitle(tr("setting.load_zero"))
            self.Load0Currentnow_labeltxt.setText(tr("setting.load_current"))
            self.Load0_pushButton.setText(tr("setting.set"))
            
            # Encoder to 0 Point Set
            self.En0_groupBox.setTitle(tr("setting.encoder_zero"))
            self.En0Positionnow_labeltxt.setText(tr("setting.encoder_position"))
            self.En0_pushButton.setText(tr("setting.set"))
            
            # Monitoring Frequency
            self.hz_groupBox.setTitle(tr("setting.monitoring_hz"))
            self.hz_label.setText(tr("setting.set_frequency"))  # ← 추가
            self.hz_set_pushButton.setText(tr("setting.set"))
            
            # Safety Limit
            self.Safty_groupBox.setTitle(tr("setting.safety"))
            self.Com_label_8.setText(tr("setting.displacement"))
            self.Com_label_10.setText(tr("setting.force"))
            self.Com_label_6.setText(tr("setting.high"))
            self.Com_label_12.setText(tr("setting.low"))
            self.Com_label_13.setText(tr("setting.displacement_limit"))
            
            # Motor Speed Setting
            self.Motspeed_groupBox.setTitle(tr("setting.motor_speed"))
            self.MotorSpeed_checkBox.setText(tr("setting.custom"))
            self.Setmotorspeed_pushButton.setText(tr("setting.set_speed"))
            
            # Jog Speed Setting
            self.groupBox_9.setTitle(tr("setting.jog_speed"))
            self.Jog_checkBox.setText(tr("setting.custom"))
            self.Setjogspeed_pushButton.setText(tr("setting.set_speed"))
            self.groupBox_10.setTitle(tr("setting.jog_control"))
            self.Jogfowerd_pushButton.setText(tr("setting.jog_forward"))
            self.Jogbackwerd_pushButton.setText(tr("setting.jog_backward"))
            
            # Pre-Tension
            self.tension_groupBox.setTitle(tr("setting.pretension"))
            self.tension_speed_label.setText(tr("setting.adjust_speed"))
            self.tension_force_label.setText(tr("setting.detect_load"))
            self.tension_start_pushButton.setText(tr("setting.start_adjust"))
            self.tension_stop_pushButton.setText(tr("setting.manual_stop"))
            
            # ===== 온도 탭 =====
            self.temp_ctrl_group.setTitle(tr("temp.monitor_control"))
            
            # 채널 체크박스
            for i in range(1, 5):
                if i in self.temp_channels:
                    ch_text = tr("temp.ch_display").format(i)
                    self.temp_channels[i]["chk"].setText(ch_text)
            
            # Control Settings
            self.temp_setting_group.setTitle(tr("temp.control_settings"))
            self.temp_sv_label.setText(tr("temp.ch1_target"))
            self.at_exec_label.setText(tr("temp.auto_tuning"))
            
            # ComboBox 항목
            self.at_exec_combo.setItemText(0, tr("temp.at_off"))
            self.at_exec_combo.setItemText(1, tr("temp.at_on"))
            
            self.temp_stability_range_label.setText(tr("temp.stability_range"))
            self.temp_stability_time_label.setText(tr("temp.stability_time"))
            self.temp_stability_enabled.setText(tr("temp.stability_enable"))
            
            # Graph View Mode
            self.temp_view_group.setTitle(tr("temp.view_mode"))
            self.temp_view_unified.setText(tr("temp.unified_view"))
            self.temp_view_split.setText(tr("temp.split_view"))
            
            # 버튼
            self.temp_start_btn.setText(tr("temp.start"))
            self.temp_stop_btn.setText(tr("temp.stop"))
            
            # Auto Scale 체크박스
            if hasattr(self, 'temp_auto_range_checkbox'):
                self.temp_auto_range_checkbox.setText(tr("temp.auto_scale"))
                self.temp_auto_range_checkbox.setToolTip(tr("temp.auto_scale_tooltip"))
                
            # ===== 실험 탭 =====
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), tr("test.basic"))
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), tr("test.torque"))
            self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), tr("test.repeat"))
            
            # Current Values
            self.testValuesWidget.setTitle(tr("test.current_values"))
            self.static_load_label.setText(tr("test.current_load"))
            self.static_pos_label.setText(tr("test.current_displacement"))
            
            # 버튼들
            self.Basicteststart_pushButton.setText(tr("test.start"))
            self.Basicteststop_pushButton.setText(tr("test.stop"))
            self.Basictestreset_pushButton.setText(tr("test.reset"))
            
            self.Torqueteststart_pushButton.setText(tr("test.start"))
            self.Torqueteststop_pushButton.setText(tr("test.stop"))
            
            # HTML 설명
            self.textEdit.setHtml(
                f"<!DOCTYPE HTML><html><head><meta name=\"qrichtext\" content=\"1\" /></head>"
                f"<body style=\"font-family:'Gulim'; font-size:9pt;\">"
                f"<p style=\"margin-top:0px; margin-bottom:0px;\">{tr('test.basic_desc')}</p>"
                f"</body></html>"
            )
            
            self.textEdit_2.setHtml(
                f"<!DOCTYPE HTML><html><head><meta name=\"qrichtext\" content=\"1\" /></head>"
                f"<body style=\"font-family:'Gulim'; font-size:9pt;\">"
                f"<p style=\"margin-top:0px; margin-bottom:0px;\">{tr('test.torque_desc')}</p>"
                f"</body></html>"
            )
            
        else:
            MainWindow.setWindowTitle(_translate("MainWindow", "PKG UTM Controller"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
