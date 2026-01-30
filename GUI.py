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
        setting_main_layout.setContentsMargins(15, 15, 15, 15)
        setting_main_layout.setSpacing(20)
        
        # ========================================================================
        # 왼쪽 컬럼 (Load0, Encoder0, Monitoring Hz, Safety)
        # ========================================================================
        left_column = QtWidgets.QVBoxLayout()
        left_column.setSpacing(15)
        
        # 1. Load to 0 Point Set
        self.Load0_groupBox = QtWidgets.QGroupBox("Load to 0 Point Set")
        self.Load0_groupBox.setMinimumSize(QtCore.QSize(320, 130))
        load0_layout = QtWidgets.QVBoxLayout(self.Load0_groupBox)
        
        load0_value_layout = QtWidgets.QHBoxLayout()
        self.Load0Currentnow_labeltxt = QtWidgets.QLabel("Load Cell Force")
        self.Load0Currentnow_label = QtWidgets.QLabel("")
        self.Load0Currentnow_label.setStyleSheet("""
            background-color: rgb(255,255,255);
            border: 1px solid #CCCCCC;
            padding: 5px;
            font-size: 11pt;
        """)
        self.Load0Currentnow_label.setMinimumHeight(30)
        load0_value_layout.addWidget(self.Load0Currentnow_labeltxt)
        load0_value_layout.addWidget(self.Load0Currentnow_label, 1)
        
        load0_button_layout = QtWidgets.QHBoxLayout()
        load0_button_layout.addStretch()
        self.Load0_pushButton = QtWidgets.QPushButton("Set")
        self.Load0_pushButton.setMinimumSize(QtCore.QSize(100, 35))
        load0_button_layout.addWidget(self.Load0_pushButton)
        load0_button_layout.addStretch()
        
        load0_layout.addLayout(load0_value_layout)
        load0_layout.addLayout(load0_button_layout)
        
        left_column.addWidget(self.Load0_groupBox)
        
        # 2. Encoder to 0 Point Set
        self.En0_groupBox = QtWidgets.QGroupBox("Encoder to 0 Point Set")
        self.En0_groupBox.setMinimumSize(QtCore.QSize(320, 130))
        en0_layout = QtWidgets.QVBoxLayout(self.En0_groupBox)
        
        en0_value_layout = QtWidgets.QHBoxLayout()
        self.En0Positionnow_labeltxt = QtWidgets.QLabel("Encoder Position")
        self.En0Positionnow_label = QtWidgets.QLabel("")
        self.En0Positionnow_label.setStyleSheet("""
            background-color: rgb(255,255,255);
            border: 1px solid #CCCCCC;
            padding: 5px;
            font-size: 11pt;
        """)
        self.En0Positionnow_label.setMinimumHeight(30)
        en0_value_layout.addWidget(self.En0Positionnow_labeltxt)
        en0_value_layout.addWidget(self.En0Positionnow_label, 1)
        
        en0_button_layout = QtWidgets.QHBoxLayout()
        en0_button_layout.addStretch()
        self.En0_pushButton = QtWidgets.QPushButton("Set")
        self.En0_pushButton.setMinimumSize(QtCore.QSize(100, 35))
        en0_button_layout.addWidget(self.En0_pushButton)
        en0_button_layout.addStretch()
        
        en0_layout.addLayout(en0_value_layout)
        en0_layout.addLayout(en0_button_layout)
        
        left_column.addWidget(self.En0_groupBox)
        
        # 3. Monitoring Frequency
        self.hz_groupBox = QtWidgets.QGroupBox("Monitoring Frequency")
        self.hz_groupBox.setMinimumSize(QtCore.QSize(320, 100))
        hz_layout = QtWidgets.QHBoxLayout(self.hz_groupBox)
        
        hz_label = QtWidgets.QLabel("Set Frequency:")
        self.hz_spinBox = QtWidgets.QSpinBox()
        self.hz_spinBox.setSuffix(" Hz")
        self.hz_spinBox.setMinimum(1)
        self.hz_spinBox.setMaximum(100)
        self.hz_spinBox.setValue(10)
        self.hz_spinBox.setMinimumHeight(30)
        
        self.hz_set_pushButton = QtWidgets.QPushButton("Set")
        self.hz_set_pushButton.setMinimumSize(QtCore.QSize(80, 30))
        
        hz_layout.addWidget(hz_label)
        hz_layout.addWidget(self.hz_spinBox, 1)
        hz_layout.addWidget(self.hz_set_pushButton)
        
        left_column.addWidget(self.hz_groupBox)
        
        # 4. Safety Limit
        self.Safty_groupBox = QtWidgets.QGroupBox("Safety Limit")
        self.Safty_groupBox.setMinimumSize(QtCore.QSize(320, 300))
        safety_layout = QtWidgets.QVBoxLayout(self.Safty_groupBox)
        
        # Displacement Section
        self.Com_label_8 = QtWidgets.QLabel("Displacement (mm)")
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.Com_label_8.setFont(font)
        
        disp_high_layout = QtWidgets.QHBoxLayout()
        self.DisplaceLimitMax_doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.DisplaceLimitMax_doubleSpinBox.setMaximum(999.99)
        self.DisplaceLimitMax_doubleSpinBox.setSingleStep(0.1)
        self.DisplaceLimitMax_doubleSpinBox.setMinimumHeight(30)
        self.Com_label_6 = QtWidgets.QLabel("High")
        disp_high_layout.addWidget(self.DisplaceLimitMax_doubleSpinBox, 1)
        disp_high_layout.addWidget(self.Com_label_6)
        
        disp_low_layout = QtWidgets.QHBoxLayout()
        self.DisplaceLimitMin_doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.DisplaceLimitMin_doubleSpinBox.setMaximum(999.99)
        self.DisplaceLimitMin_doubleSpinBox.setSingleStep(0.1)
        self.DisplaceLimitMin_doubleSpinBox.setMinimumHeight(30)
        self.Com_label_12 = QtWidgets.QLabel("Low")
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
        self.ForceLimitMax_doubleSpinBox = QtWidgets.QDoubleSpinBox()
        self.ForceLimitMax_doubleSpinBox.setMaximum(999.99)
        self.ForceLimitMax_doubleSpinBox.setSingleStep(0.1)
        self.ForceLimitMax_doubleSpinBox.setMinimumHeight(30)
        self.Com_label_13 = QtWidgets.QLabel("Displacement")
        force_layout.addWidget(self.ForceLimitMax_doubleSpinBox, 1)
        force_layout.addWidget(self.Com_label_13)
        
        self.Com_label_14 = QtWidgets.QLabel("Displacement")
        
        safety_layout.addWidget(self.Com_label_8)
        safety_layout.addLayout(disp_high_layout)
        safety_layout.addLayout(disp_low_layout)
        safety_layout.addSpacing(10)
        safety_layout.addWidget(line)
        safety_layout.addSpacing(10)
        safety_layout.addWidget(self.Com_label_10)
        safety_layout.addLayout(force_layout)
        safety_layout.addWidget(self.Com_label_14)
        safety_layout.addStretch()
        
        left_column.addWidget(self.Safty_groupBox)
        left_column.addStretch()
        
        # ========================================================================
        # 오른쪽 컬럼 (Motor Speed, Jog Speed, Pre-Tension)
        # ========================================================================
        right_column = QtWidgets.QVBoxLayout()
        right_column.setSpacing(15)
        
        # 1. Motor Speed Setting
        self.Motspeed_groupBox = QtWidgets.QGroupBox("Motor Speed Setting")
        self.Motspeed_groupBox.setMinimumSize(QtCore.QSize(400, 280))
        motor_layout = QtWidgets.QVBoxLayout(self.Motspeed_groupBox)
        
        # 사용자 지정 입력
        motor_input_layout = QtWidgets.QHBoxLayout()
        self.MotorSpeed_checkBox = QtWidgets.QCheckBox("사용자 지정")
        self.MotorSpeed_spinBox = QtWidgets.QSpinBox()
        self.MotorSpeed_spinBox.setMaximum(5000)
        self.MotorSpeed_spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.MotorSpeed_spinBox.setMinimumHeight(30)
        self.MotorSpeedUnit_label = QtWidgets.QLabel("[um/sec]")
        
        motor_input_layout.addStretch()
        motor_input_layout.addWidget(self.MotorSpeed_checkBox)
        motor_input_layout.addWidget(self.MotorSpeed_spinBox)
        motor_input_layout.addWidget(self.MotorSpeedUnit_label)
        motor_input_layout.addStretch()
        
        # 프리셋 라디오 버튼
        motor_preset_layout = QtWidgets.QGridLayout()
        motor_preset_layout.setSpacing(10)
        
        self.Motor10_radioButton = QtWidgets.QRadioButton("10 um/sec")
        self.Motor20_radioButton = QtWidgets.QRadioButton("20 um/sec")
        self.Motor30_radioButton = QtWidgets.QRadioButton("30 um/sec")
        self.Motor40_radioButton = QtWidgets.QRadioButton("40 um/sec")
        self.Motor50_radioButton = QtWidgets.QRadioButton("50 um/sec")
        self.Motor100_radioButton = QtWidgets.QRadioButton("100 um/sec")
        self.Motor200_radioButton = QtWidgets.QRadioButton("200 um/sec")
        self.Motor300_radioButton = QtWidgets.QRadioButton("300 um/sec")
        
        motor_preset_layout.addWidget(self.Motor10_radioButton, 0, 0)
        motor_preset_layout.addWidget(self.Motor20_radioButton, 1, 0)
        motor_preset_layout.addWidget(self.Motor30_radioButton, 2, 0)
        motor_preset_layout.addWidget(self.Motor40_radioButton, 3, 0)
        motor_preset_layout.addWidget(self.Motor50_radioButton, 0, 1)
        motor_preset_layout.addWidget(self.Motor100_radioButton, 1, 1)
        motor_preset_layout.addWidget(self.Motor200_radioButton, 2, 1)
        motor_preset_layout.addWidget(self.Motor300_radioButton, 3, 1)
        
        # Set Speed 버튼
        motor_button_layout = QtWidgets.QHBoxLayout()
        motor_button_layout.addStretch()
        self.Setmotorspeed_pushButton = QtWidgets.QPushButton("Set Speed")
        self.Setmotorspeed_pushButton.setMinimumSize(QtCore.QSize(100, 35))
        motor_button_layout.addWidget(self.Setmotorspeed_pushButton)
        motor_button_layout.addStretch()
        
        motor_layout.addLayout(motor_input_layout)
        motor_layout.addLayout(motor_preset_layout)
        motor_layout.addLayout(motor_button_layout)
        
        right_column.addWidget(self.Motspeed_groupBox)
        
        # 2. Jog Speed Setting
        self.groupBox_9 = QtWidgets.QGroupBox("Jog Speed Setting")
        self.groupBox_9.setMinimumSize(QtCore.QSize(400, 350))
        jog_main_layout = QtWidgets.QVBoxLayout(self.groupBox_9)
        
        # Jog 속도 설정 부분
        jog_speed_widget = QtWidgets.QWidget()
        jog_layout = QtWidgets.QVBoxLayout(jog_speed_widget)
        jog_layout.setContentsMargins(0, 0, 0, 0)
        
        jog_input_layout = QtWidgets.QHBoxLayout()
        self.Jog_checkBox = QtWidgets.QCheckBox("사용자 지정")
        self.Jog_spinBox = QtWidgets.QSpinBox()
        self.Jog_spinBox.setMaximum(5000)
        self.Jog_spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.Jog_spinBox.setMinimumHeight(30)
        self.Com_label_15 = QtWidgets.QLabel("[um/sec]")
        
        jog_input_layout.addStretch()
        jog_input_layout.addWidget(self.Jog_checkBox)
        jog_input_layout.addWidget(self.Jog_spinBox)
        jog_input_layout.addWidget(self.Com_label_15)
        jog_input_layout.addStretch()
        
        jog_preset_layout = QtWidgets.QGridLayout()
        jog_preset_layout.setSpacing(10)
        
        self.jog10_radioButton = QtWidgets.QRadioButton("10 um/sec")
        self.jog20_radioButton = QtWidgets.QRadioButton("20 um/sec")
        self.jog30_radioButton = QtWidgets.QRadioButton("30 um/sec")
        self.jog40_radioButton = QtWidgets.QRadioButton("40 um/sec")
        self.jog50_radioButton = QtWidgets.QRadioButton("50 um/sec")
        self.jog100_radioButton = QtWidgets.QRadioButton("100 um/sec")
        self.jog200_radioButton = QtWidgets.QRadioButton("200 um/sec")
        self.jog500_radioButton = QtWidgets.QRadioButton("500 um/sec")
        
        jog_preset_layout.addWidget(self.jog10_radioButton, 0, 0)
        jog_preset_layout.addWidget(self.jog20_radioButton, 1, 0)
        jog_preset_layout.addWidget(self.jog30_radioButton, 2, 0)
        jog_preset_layout.addWidget(self.jog40_radioButton, 3, 0)
        jog_preset_layout.addWidget(self.jog50_radioButton, 0, 1)
        jog_preset_layout.addWidget(self.jog100_radioButton, 1, 1)
        jog_preset_layout.addWidget(self.jog200_radioButton, 2, 1)
        jog_preset_layout.addWidget(self.jog500_radioButton, 3, 1)
        
        jog_button_layout = QtWidgets.QHBoxLayout()
        jog_button_layout.addStretch()
        self.Setjogspeed_pushButton = QtWidgets.QPushButton("Set Speed")
        self.Setjogspeed_pushButton.setMinimumSize(QtCore.QSize(100, 35))
        jog_button_layout.addWidget(self.Setjogspeed_pushButton)
        jog_button_layout.addStretch()
        
        jog_layout.addLayout(jog_input_layout)
        jog_layout.addLayout(jog_preset_layout)
        jog_layout.addLayout(jog_button_layout)
        
        # Jog 제어 버튼
        self.groupBox_10 = QtWidgets.QGroupBox("Jog Control")
        self.groupBox_10.setMinimumHeight(80)
        jog_control_layout = QtWidgets.QHBoxLayout(self.groupBox_10)
        jog_control_layout.addStretch()
        
        self.Jogfowerd_pushButton = QtWidgets.QPushButton("Jog +")
        self.Jogfowerd_pushButton.setMinimumSize(QtCore.QSize(100, 40))
        
        self.Jogbackwerd_pushButton = QtWidgets.QPushButton("Jog -")
        self.Jogbackwerd_pushButton.setMinimumSize(QtCore.QSize(100, 40))
        
        jog_control_layout.addWidget(self.Jogfowerd_pushButton)
        jog_control_layout.addWidget(self.Jogbackwerd_pushButton)
        jog_control_layout.addStretch()
        
        jog_main_layout.addWidget(jog_speed_widget)
        jog_main_layout.addWidget(self.groupBox_10)
        
        right_column.addWidget(self.groupBox_9)
        
        # 3. Pre-Tension
        self.tension_groupBox = QtWidgets.QGroupBox("Pre-Tension")
        self.tension_groupBox.setMinimumSize(QtCore.QSize(400, 170))
        tension_layout = QtWidgets.QFormLayout(self.tension_groupBox)
        tension_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        tension_layout.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        tension_layout.setVerticalSpacing(15)
        
        self.tension_speed_spinBox = QtWidgets.QDoubleSpinBox()
        self.tension_speed_spinBox.setSuffix(" um/sec")
        self.tension_speed_spinBox.setMinimum(10)
        self.tension_speed_spinBox.setMaximum(1000.0)
        self.tension_speed_spinBox.setValue(10.0)
        self.tension_speed_spinBox.setSingleStep(10.0)
        self.tension_speed_spinBox.setMinimumHeight(35)
        
        self.tension_force_spinBox = QtWidgets.QDoubleSpinBox()
        self.tension_force_spinBox.setSuffix(" N")
        self.tension_force_spinBox.setMinimum(-999)
        self.tension_force_spinBox.setMaximum(999)
        self.tension_force_spinBox.setValue(0.1)
        self.tension_force_spinBox.setDecimals(3)
        self.tension_force_spinBox.setSingleStep(0.1)
        self.tension_force_spinBox.setMinimumHeight(35)
        
        tension_layout.addRow("조정 속도:", self.tension_speed_spinBox)
        tension_layout.addRow("감지 하중:", self.tension_force_spinBox)
        
        tension_button_layout = QtWidgets.QHBoxLayout()
        tension_button_layout.addStretch()
        
        self.tension_start_pushButton = QtWidgets.QPushButton("조정 시작")
        self.tension_start_pushButton.setMinimumSize(QtCore.QSize(100, 35))
        tension_button_layout.addWidget(self.tension_start_pushButton)
        
        self.tension_stop_pushButton = QtWidgets.QPushButton("수동 정지")
        self.tension_stop_pushButton.setMinimumSize(QtCore.QSize(100, 35))
        tension_button_layout.addWidget(self.tension_stop_pushButton)
        
        tension_button_layout.addStretch()
        tension_layout.addRow(tension_button_layout)
        
        right_column.addWidget(self.tension_groupBox)
        right_column.addStretch()
        
        # 메인 레이아웃에 좌우 컬럼 추가
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
        self.temp_sv_input = QtWidgets.QDoubleSpinBox()
        self.temp_sv_input.setRange(0, 500)
        self.temp_sv_input.setDecimals(1)
        self.temp_sv_input.setSuffix(" °C")
        self.temp_sv_input.setMinimumHeight(35)
        self.temp_setting_form.addRow("CH1 Target:", self.temp_sv_input)

        # 오토튜닝 ON/OFF
        self.at_exec_combo = QtWidgets.QComboBox()
        self.at_exec_combo.addItems(["OFF (정지)", "ON (실행)"])
        self.at_exec_combo.setMinimumHeight(35)
        self.at_exec_combo.setCurrentIndex(1)
        self.temp_setting_form.addRow("오토 튜닝:", self.at_exec_combo)

        # 구분선
        line_stabilization = QtWidgets.QFrame()
        line_stabilization.setFrameShape(QtWidgets.QFrame.HLine)
        line_stabilization.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.temp_setting_form.addRow(line_stabilization)

        # 안정화 범위 설정
        self.temp_stability_range = QtWidgets.QDoubleSpinBox()
        self.temp_stability_range.setRange(0.1, 50.0)
        self.temp_stability_range.setDecimals(1)
        self.temp_stability_range.setSuffix(" °C")
        self.temp_stability_range.setValue(2.0)
        self.temp_stability_range.setMinimumHeight(35)
        self.temp_setting_form.addRow("안정화 범위 (±):", self.temp_stability_range)

        # 안정화 시간 설정
        self.temp_stability_time = QtWidgets.QSpinBox()
        self.temp_stability_time.setRange(1, 60)
        self.temp_stability_time.setSuffix(" 분")
        self.temp_stability_time.setValue(5)
        self.temp_stability_time.setMinimumHeight(35)
        self.temp_setting_form.addRow("안정화 시간:", self.temp_stability_time)

        # 안정화 감지 활성화
        self.temp_stability_enabled = QtWidgets.QCheckBox("안정화 감지 활성화")
        self.temp_stability_enabled.setChecked(True)
        self.temp_stability_enabled.setMinimumHeight(35)
        self.temp_setting_form.addRow(self.temp_stability_enabled)

        self.ctrl_vbox.addWidget(self.temp_setting_group)
        
        # 그래프 뷰 모드 선택
        self.temp_view_group = QtWidgets.QGroupBox("Graph View Mode")
        self.temp_view_layout = QtWidgets.QVBoxLayout(self.temp_view_group)

        self.temp_view_unified = QtWidgets.QRadioButton("통합 뷰 (4채널 한 화면)")
        self.temp_view_unified.setChecked(True)
        self.temp_view_layout.addWidget(self.temp_view_unified)

        self.temp_view_split = QtWidgets.QRadioButton("분할 뷰 (4개 그래프)")
        self.temp_view_layout.addWidget(self.temp_view_split)

        self.ctrl_vbox.addWidget(self.temp_view_group)
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
        font.setPointSize(10)
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

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "UTM Control System"))
        
        self.Main_tabWidget.setTabText(self.Main_tabWidget.indexOf(self.tab_2), _translate("MainWindow", "COM Set"))
        self.Main_tabWidget.setTabText(self.Main_tabWidget.indexOf(self.tab), _translate("MainWindow", "Setting"))
        self.Main_tabWidget.setTabText(self.Main_tabWidget.indexOf(self.tab_new), _translate("MainWindow", "Temp"))
        
        self.textEdit.setHtml(_translate("MainWindow", 
            "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
            "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
            "p, li { white-space: pre-wrap; }\n"
            "</style></head><body style=\" font-family:\'Gulim\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
            "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">"
            "<span style=\" font-size:10pt; font-weight:600;\">Basic Tensile Test</span><span style=\" font-size:10pt;\"><br />"
            "The specimen is stretched until fracture, and the torque value observed during the test is recorded and analyzed.</span></p></body></html>"))
        
        self.textEdit_2.setHtml(_translate("MainWindow",
            "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
            "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
            "p, li { white-space: pre-wrap; }\n"
            "</style></head><body style=\" font-family:\'Gulim\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
            "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">"
            "<span style=\" font-size:10pt; font-weight:600;\">Torque-Controlled Tensile Test</span><span style=\" font-size:10pt;\"><br />"
            "A constant input torque is applied to the specimen, and its resulting deformation and behavior are observed.</span></p></body></html>"))
        
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), _translate("MainWindow", "Basic Tensile Test"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), _translate("MainWindow", "Torque Tensile Test"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_6), _translate("MainWindow", "Repeat Tensile Test"))
        self.Main_tabWidget.setTabText(self.Main_tabWidget.indexOf(self.tab_3), _translate("MainWindow", "Test"))
        self.Main_tabWidget.setTabText(self.Main_tabWidget.indexOf(self.tab_data), _translate("MainWindow", "Data"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
