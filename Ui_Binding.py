# Ui_Binding.py

def bind_main_signals(ui, controller):

    # Encoder 초기화 버튼 연결
    ui.En0_pushButton.clicked.connect(controller.on_zero_encoder_clicked)

    # Jog 버튼 연결
    ui.Jogfowerd_pushButton.pressed.connect(
        lambda: controller.motor.jog_forward() if controller.motor else print("[UI] Motor not connected")
    )
    ui.Jogfowerd_pushButton.released.connect(
        lambda: controller.motor.stop_motor() if controller.motor else None
    )
    ui.Jogbackwerd_pushButton.pressed.connect(
        lambda: controller.motor.jog_backward() if controller.motor else print("[UI] Motor not connected")
    )
    ui.Jogbackwerd_pushButton.released.connect(
        lambda: controller.motor.stop_motor() if controller.motor else None
    )

    # Jog 모드 설정
    ui.Jog_checkBox.stateChanged.connect(controller.speed_controller.toggle_jog_mode)
    ui.Setjogspeed_pushButton.clicked.connect(controller.speed_controller.set_jog_speed)
    ui.Jog_checkBox.stateChanged.connect(controller.speed_controller.toggle_jog_speed_mode)

    # Jog 라디오 버튼 연결
    ui.jog10_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_jog_speed(10, checked))
    ui.jog20_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_jog_speed(20, checked))
    ui.jog30_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_jog_speed(30, checked))
    ui.jog40_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_jog_speed(40, checked))
    ui.jog50_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_jog_speed(50, checked))
    ui.jog100_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_jog_speed(100, checked))
    ui.jog200_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_jog_speed(200, checked))
    ui.jog500_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_jog_speed(500, checked))

    # Motor 속도 설정
    ui.MotorSpeed_checkBox.stateChanged.connect(controller.speed_controller.toggle_motor_speed_mode)
    ui.Setmotorspeed_pushButton.clicked.connect(controller.speed_controller.set_run_speed)

    # Motor 라디오 버튼 연결
    ui.Motor10_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_run_speed(10, checked))
    ui.Motor20_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_run_speed(20, checked))
    ui.Motor30_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_run_speed(30, checked))
    ui.Motor40_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_run_speed(40, checked))
    ui.Motor50_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_run_speed(50, checked))
    ui.Motor100_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_run_speed(100, checked))
    ui.Motor200_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_run_speed(200, checked))
    ui.Motor300_radioButton.toggled.connect(lambda checked: controller.speed_controller.set_fixed_run_speed(300, checked))

    # (controller.basic_test는 None일 수 있으므로 lambda로 변경)
    # (이 연결은 Main.py의 __init__에서 on_basic_test_stop으로 다시 바인딩됩니다.)
    ui.Basicteststop_pushButton.clicked.connect(
        lambda: controller.basic_test.stop() if controller.basic_test else print("[UI] Test not started")
    )