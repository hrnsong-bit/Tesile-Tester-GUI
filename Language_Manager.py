# Language_Manager.py
import logging
from PyQt5 import QtCore, QtWidgets
from Settings_Manager import SettingsManager

logger = logging.getLogger(__name__)

class LanguageManager(QtCore.QObject):
    """
    애플리케이션 언어를 관리하는 클래스
    """
    
    # 언어 변경 시그널
    language_changed = QtCore.pyqtSignal(str)  # 언어 코드 전달
    
    # 지원 언어
    LANGUAGES = {
        "en": "English",
        "KR": "한국어"
    }
    
    def __init__(self):
        super().__init__()
        self.settings_mgr = SettingsManager()
        self.current_language = "en"  # 기본값
        
        # 저장된 언어 불러오기
        self._load_saved_language()
    
    def _load_saved_language(self):
        """저장된 언어 설정 불러오기"""
        try:
            saved_lang = self.settings_mgr.load_language()
            if saved_lang in self.LANGUAGES:
                self.current_language = saved_lang
                logger.info(f"저장된 언어 복원: {self.LANGUAGES[saved_lang]}")
            else:
                logger.warning(f"알 수 없는 언어 코드: {saved_lang}, 기본값 사용")
        except Exception as e:
            logger.error(f"언어 설정 불러오기 실패: {e}")
    
    def set_language(self, lang_code: str) -> bool:
        """
        언어 변경
        
        Args:
            lang_code: "en" 또는 "KR"
            
        Returns:
            bool: 성공 여부
        """
        if lang_code not in self.LANGUAGES:
            logger.error(f"지원하지 않는 언어: {lang_code}")
            return False
        
        if lang_code == self.current_language:
            logger.debug("이미 선택된 언어입니다.")
            return True
        
        try:
            self.current_language = lang_code
            
            # 설정 저장
            self.settings_mgr.save_language(lang_code)
            
            # 시그널 발생
            self.language_changed.emit(lang_code)
            
            logger.info(f"언어 변경: {self.LANGUAGES[lang_code]}")
            return True
            
        except Exception as e:
            logger.error(f"언어 변경 실패: {e}")
            return False
    
    def get_current_language(self) -> str:
        """현재 언어 코드 반환"""
        return self.current_language
    
    def get_current_language_name(self) -> str:
        """현재 언어 이름 반환"""
        return self.LANGUAGES.get(self.current_language, "Unknown")
    
    def translate(self, key: str) -> str:
        """
        키에 해당하는 번역 텍스트 반환
        
        Args:
            key: 번역 키
            
        Returns:
            str: 번역된 텍스트
        """
        return TRANSLATIONS.get(key, {}).get(self.current_language, key)


# ========================================================================
# 번역 사전
# ========================================================================
TRANSLATIONS = {
    # 메뉴
    "menu.font": {"en": "Font", "KR": "글꼴"},
    "menu.about": {"en": "About", "KR": "정보"},
    "menu.language": {"en": "Language", "KR": "언어"},
    
    # 탭
    "tab.com_set": {"en": "COM Set", "KR": "COM 설정"},
    "tab.setting": {"en": "Setting", "KR": "설정"},
    "tab.temp": {"en": "Temp", "KR": "온도"},
    "tab.test": {"en": "Test", "KR": "실험"},
    "tab.data": {"en": "Data", "KR": "데이터"},
    
    # COM 그룹
    "com.motor": {"en": "Motor", "KR": "모터"},
    "com.loadcell": {"en": "Load Cell", "KR": "로드셀"},
    "com.temp": {"en": "Temp Controller", "KR": "온도 제어기"},
    "com.port": {"en": "COM port", "KR": "COM 포트"},
    "com.baudrate": {"en": "Baud-rate", "KR": "통신 속도"},
    "com.refresh": {"en": "Refresh", "KR": "새로고침"},
    "com.connect": {"en": "Connect", "KR": "연결"},
    "com.disconnect": {"en": "Disconnect", "KR": "연결 해제"},
    
    # Setting 탭
    "setting.load_zero": {"en": "Load to 0 Point Set", "KR": "하중 영점 설정"},
    "setting.load_current": {"en": "Load Cell Force", "KR": "로드셀 하중"},
    "setting.encoder_zero": {"en": "Encoder to 0 Point Set", "KR": "엔코더 영점 설정"},
    "setting.encoder_position": {"en": "Encoder Position", "KR": "엔코더 위치"},
    "setting.set": {"en": "Set", "KR": "설정"},
    
    "setting.monitoring_hz": {"en": "Monitoring Frequency", "KR": "모니터링 주파수"},
    "setting.set_frequency": {"en": "Set Frequency:", "KR": "주파수 설정:"},
    
    "setting.safety": {"en": "Safety Limit", "KR": "안전 제한"},
    "setting.displacement": {"en": "Displacement (mm)", "KR": "변위 (mm)"},
    "setting.force": {"en": "Force (N)", "KR": "하중 (N)"},
    "setting.high": {"en": "High", "KR": "상한"},
    "setting.low": {"en": "Low", "KR": "하한"},
    "setting.displacement_limit": {"en": "Displacement", "KR": "변위"},
    
    "setting.motor_speed": {"en": "Motor Speed Setting", "KR": "모터 속도 설정"},
    "setting.custom": {"en": "Custom", "KR": "사용자 지정"},
    "setting.set_speed": {"en": "Set Speed", "KR": "속도 설정"},
    
    "setting.jog_speed": {"en": "Jog Speed Setting", "KR": "조그 속도 설정"},
    "setting.jog_control": {"en": "Jog Control", "KR": "조그 제어"},
    "setting.jog_forward": {"en": "Compression", "KR": "압축"},
    "setting.jog_backward": {"en": "Tensile", "KR": "인장"},
    
    "setting.pretension": {"en": "Pre-Tension", "KR": "초기 장력"},
    "setting.adjust_speed": {"en": "Adjust Speed:", "KR": "조정 속도:"},
    "setting.detect_load": {"en": "Detect Load:", "KR": "감지 하중:"},
    "setting.start_adjust": {"en": "Start Adjust", "KR": "조정 시작"},
    "setting.manual_stop": {"en": "Manual Stop", "KR": "수동 정지"},
    
    # 온도 탭
    "temp.monitor_control": {"en": "Channel Monitor & Control", "KR": "채널 모니터 및 제어"},
    "temp.ch_display": {"en": "CH {0} Display", "KR": "CH {0} 표시"},
    "temp.control_settings": {"en": "Control Settings", "KR": "제어 설정"},
    "temp.ch1_target": {"en": "CH1 Target:", "KR": "CH1 목표:"},
    "temp.auto_tuning": {"en": "Auto Tuning:", "KR": "오토 튜닝:"},
    "temp.at_off": {"en": "OFF (Stop)", "KR": "OFF (정지)"},
    "temp.at_on": {"en": "ON (Running)", "KR": "ON (실행)"},
    "temp.stability_range": {"en": "Stability Range (±):", "KR": "안정화 범위 (±):"},
    "temp.stability_time": {"en": "Stability Time:", "KR": "안정화 시간:"},
    "temp.stability_enable": {"en": "Enable Stability Detection", "KR": "안정화 감지 활성화"},
    "temp.view_mode": {"en": "Graph View Mode", "KR": "그래프 뷰 모드"},
    "temp.unified_view": {"en": "Unified View (4 channels)", "KR": "통합 뷰 (4채널)"},
    "temp.split_view": {"en": "Split View (4 graphs)", "KR": "분할 뷰 (4개 그래프)"},
    "temp.start": {"en": "Start", "KR": "시작"},
    "temp.stop": {"en": "Stop", "KR": "정지"},
    "temp.minute": {"en": "min", "KR": "분"},
    "temp.celsius": {"en": "°C", "KR": "°C"},
    
    # 실험 탭
    "test.basic": {"en": "Basic Tensile Test", "KR": "기본 인장 실험"},
    "test.torque": {"en": "Torque Tensile Test", "KR": "토크 인장 실험"},
    "test.repeat": {"en": "Repeat Tensile Test", "KR": "반복 인장 실험"},
    
    "test.current_values": {"en": "Current Values", "KR": "현재 값"},
    "test.current_load": {"en": "Current Load (N):", "KR": "현재 하중 (N):"},
    "test.current_displacement": {"en": "Current Displacement (um):", "KR": "현재 변위 (um):"},
    "test.start": {"en": "Start", "KR": "시작"},
    "test.stop": {"en": "Stop", "KR": "정지"},
    "test.reset": {"en": "Reset", "KR": "리셋"},
    
    "test.basic_desc": {
        "en": "<b>Basic Tensile Test</b><br/>The specimen is stretched until fracture, and the torque value observed during the test is recorded and analyzed.",
        "KR": "<b>기본 인장 실험</b><br/>시편을 파단될 때까지 늘이고, 실험 중 관찰된 토크 값을 기록하고 분석합니다."
    },
    
    "test.torque_desc": {
        "en": "<b>Torque-Controlled Tensile Test</b><br/>A constant input torque is applied to the specimen, and its resulting deformation and behavior are observed.",
        "KR": "<b>토크 제어 인장 실험</b><br/>시편에 일정한 입력 토크를 가하고, 그에 따른 변형 및 거동을 관찰합니다."
    },
    
    # ===== Data 탭 =====
    # SS Curve Generator
    "data.ss_curve": {"en": "SS Curve Generator", "KR": "응력-변형률 곡선 생성기"},
    "data.load_settings": {"en": "Load · Settings", "KR": "파일 로드 · 설정"},
    "data.load_utm": {"en": "Load UTM CSV", "KR": "UTM CSV 로드"},
    "data.load_dic": {"en": "Load DIC CSV", "KR": "DIC CSV 로드"},
    "data.utm_load": {"en": "UTM Load (N):", "KR": "UTM 하중 (N):"},
    "data.dic_strain": {"en": "DIC Strain (%):", "KR": "DIC 변형률 (%):"},
    "data.merge_tol": {"en": "Merge tol (s):", "KR": "병합 허용오차 (s):"},
    "data.calc_yield": {"en": "Calc Yield Strength (0.2%)", "KR": "항복강도 계산 (0.2%)"},
    "data.geometry": {"en": "Geometry:", "KR": "시편 치수:"},
    "data.generate_curve": {"en": "Generate S–S Curve", "KR": "응력-변형률 곡선 생성"},
    "data.save_csv": {"en": "Save CSV", "KR": "CSV 저장"},
    "data.save_graph": {"en": "Save Graph", "KR": "그래프 저장"},
    "data.results": {"en": "Results", "KR": "결과"},
    "data.uts": {"en": "UTS: - (MPa) | YS: - (MPa)", "KR": "인장강도: - (MPa) | 항복강도: - (MPa)"},
    
    # CSV Preprocessor
    "data.preprocessor": {"en": "CSV Preprocessor", "KR": "CSV 전처리기"},
    "data.load_csv": {"en": "Load CSV", "KR": "CSV 로드"},
    "data.file": {"en": "File: -", "KR": "파일: -"},
    "data.x_column": {"en": "X column:", "KR": "X축 :"},
    "data.y_column": {"en": "Y column:", "KR": "Y축 :"},
    "data.set_start": {"en": "Set as Start", "KR": "시작점 설정"},
    "data.reset_data": {"en": "Reset Data", "KR": "데이터 초기화"},
    "data.delete_inside": {"en": "Delete Inside Range", "KR": "범위 내부 삭제"},
    "data.delete_outside": {"en": "Delete Outside Range (Crop)", "KR": "범위 외부 삭제 (자르기)"},
    "data.export": {"en": "Export Processed CSV", "KR": "처리된 CSV 내보내기"},
    
    # Multi Compare
    "data.multi_compare": {"en": "Multi Compare", "KR": "다중 곡선 비교"},
    "data.load_multiple": {"en": "Load Multiple UTM + DIC", "KR": "다중 UTM+DIC 로드"},
    "data.add_pair": {"en": "Add", "KR": "추가"},
    "data.edit_label": {"en": "Edit Label", "KR": "라벨 수정"},
    "data.remove_pair": {"en": "Remove", "KR": "제거"},
    "data.default_tol": {"en": "Default merge tol (s):", "KR": "전체 병합 허용오차 (s):"},
    "data.per_curve_tol": {"en": "Per-curve tol (s):", "KR": "곡선별 허용오차 (s):"},
    "data.manual_fit": {"en": "Manual fit range (%):", "KR": "수동 피팅 범위 (%):"},
    "data.fit_by_range": {"en": "Fit by Range", "KR": "범위로 피팅"},
    "data.generate_multi": {"en": "Generate Multi Curve", "KR": "다중 곡선 생성"},
    "data.properties": {"en": "Properties", "KR": "물성값"},
    "data.select_utm": {"en": "Select UTM CSV", "KR": "UTM CSV 선택"},
    "data.select_dic": {"en": "Select DIC CSV", "KR": "DIC CSV 선택"},
    "data.select_multiple_utm": {"en": "Select multiple UTM CSVs", "KR": "여러 UTM CSV 선택"},
    "data.select_multiple_dic": {"en": "Select multiple DIC CSVs", "KR": "여러 DIC CSV 선택"},

    "data.pairs_label": {"en": "Pairs (label = auto-extracted):", "KR": "쌍 목록 (라벨 = 자동 추출):"},
    "data.enter_pair_label": {"en": "Enter Pair Label", "KR": "쌍 라벨 입력"},
    "data.label_for_pair": {"en": "Label for this pair:", "KR": "이 쌍의 라벨:"},
    "data.enter_new_label": {"en": "Enter new label:", "KR": "새 라벨 입력:"},

    "data.pair_item_format": {"en": "{:02d}. {} | tol={:.3f}s", "KR": "{:02d}. {} | 허용오차={:.3f}초"},
    "data.summary_format": {"en": "UTM: {}, DIC: {}, Pairs: {}", "KR": "UTM: {}개, DIC: {}개, 쌍: {}개"},
    # 속성 패널
    "data.properties": {"en": "Properties", "KR": "물성값"},
    "data.e_value": {"en": "E={:.3f} GPa", "KR": "탄성계수={:.3f} GPa"},
    "data.e_value_na": {"en": "E=–", "KR": "탄성계수=–"},
    "data.uts_value": {"en": "UTS={:.1f}", "KR": "인장강도={:.1f}"},
    "data.ys_value": {"en": "YS={:.1f}", "KR": "항복강도={:.1f}"},
    "data.ys_value_na": {"en": "YS=–", "KR": "항복강도=–"},

    # 메시지
    "msg.cancelled": {"en": "Cancelled", "KR": "취소됨"},
    "msg.dic_cancelled": {"en": "DIC file selection cancelled.", "KR": "DIC 파일 선택이 취소되었습니다."},
    "msg.invalid_selection": {"en": "Invalid Selection", "KR": "잘못된 선택"},
    "msg.files_must_different": {"en": "UTM and DIC files must be different!", "KR": "UTM과 DIC 파일은 서로 달라야 합니다!"},
    "msg.same_filename_warning": {"en": "Same Filename Warning", "KR": "동일 파일명 경고"},
    "msg.same_filename_desc": {
        "en": "UTM and DIC have identical filenames:\n'{}'\n\nContinue anyway?",
        "KR": "UTM과 DIC 파일명이 동일합니다:\n'{}'\n\n계속하시겠습니까?"
    },
    "msg.duplicate_label": {"en": "Duplicate Label", "KR": "중복된 라벨"},
    "msg.duplicate_label_desc": {
        "en": "Label '{}' already exists. Auto-incrementing.",
        "KR": "라벨 '{}'이(가) 이미 존재합니다. 자동으로 번호를 추가합니다."
    },
    "msg.choose_different_name": {
        "en": "Label '{}' exists. Choose different name.",
        "KR": "라벨 '{}'이(가) 존재합니다. 다른 이름을 선택하세요."
    },
    "msg.pair_added": {"en": "Pair Added", "KR": "쌍 추가됨"},
    "msg.pair_added_desc": {
        "en": "Added:\n  {}\n  UTM: {}\n  DIC: {}",
        "KR": "추가됨:\n  {}\n  UTM: {}\n  DIC: {}"
    },
    "msg.no_selection": {"en": "No Selection", "KR": "선택 없음"},
    "msg.select_pair": {"en": "Please select a pair.", "KR": "쌍을 선택하세요."},
    "msg.pair_removed": {"en": "Pair Removed", "KR": "쌍 제거됨"},
    "msg.pair_removed_desc": {"en": "Removed: {}", "KR": "제거됨: {}"},
    "msg.invalid_pairs": {"en": "Invalid Pairs Detected", "KR": "잘못된 쌍 감지"},
    "msg.invalid_pairs_desc": {
        "en": "Skipped {} pair(s) where files were identical.",
        "KR": "파일이 동일한 {}개 쌍을 건너뛰었습니다."
    },
    "msg.no_valid_pairs": {"en": "No Valid Pairs", "KR": "유효한 쌍 없음"},
    "msg.no_valid_pairs_found": {"en": "No valid pairs found.", "KR": "유효한 쌍을 찾을 수 없습니다."},
    "msg.load_complete": {"en": "Load Complete", "KR": "로드 완료"},
    "msg.pairs_loaded": {"en": "Loaded {} pair(s).", "KR": "{}개 쌍을 로드했습니다."},
    "msg.info": {"en": "Info", "KR": "정보"},
    "msg.saved": {"en": "Saved", "KR": "저장됨"},
    "msg.saved_desc": {"en": "Saved:\n{}", "KR": "저장됨:\n{}"},
    "msg.error": {"en": "Error", "KR": "오류"},
    "msg.save_failed": {"en": "Failed:\n{}", "KR": "실패:\n{}"},

    # Geometry Input
    "data.width": {"en": "Width [mm]", "KR": "폭 [mm]"},
    "data.thickness": {"en": "Thickness [mm]", "KR": "두께 [mm]"},
    "data.gauge": {"en": "Gauge [mm]", "KR": "게이지 길이 [mm]"},
    "data.preset": {"en": "Preset:", "KR": "프리셋:"},
    "data.save_preset": {"en": "Save", "KR": "저장"},
    "data.delete_preset": {"en": "Del", "KR": "삭제"},
    
    # Messages
    "msg.connection_success": {"en": "Connection Success", "KR": "연결 성공"},
    "msg.connection_failed": {"en": "Connection Failed", "KR": "연결 실패"},
    "msg.disconnection": {"en": "Disconnection", "KR": "연결 해제"},
    "msg.port_required": {"en": "Port Selection Required", "KR": "포트 선택 필요"},
    "msg.select_port": {"en": "Please select a port or connect the device.", "KR": "포트를 선택하거나 장치를 연결하세요."},
    "msg.not_connected": {"en": "{0} is not connected.", "KR": "{0}이(가) 연결되지 않았습니다."},
    
    "msg.font_changed": {"en": "Font Size Changed", "KR": "글꼴 크기 변경"},
    "msg.font_changed_desc": {
        "en": "Font size changed to {0}.\nSome elements will be applied after restarting the program.",
        "KR": "글꼴 크기가 {0}(으)로 변경되었습니다.\n일부 요소는 프로그램 재시작 후 적용됩니다."
    },
    
    "msg.language_changed": {"en": "Language Changed", "KR": "언어 변경"},
    "msg.language_changed_desc": {
        "en": "Language changed to {0}.\nPlease restart the program for full effect.",
        "KR": "언어가 {0}(으)로 변경되었습니다.\n모든 변경사항을 적용하려면 프로그램을 재시작하세요."
    },
    
    # Window title
    "window.title": {"en": "PKG UTM Controller", "KR": "PKG UTM 제어 시스템"},

    # About 다이얼로그
    "about.title": {"en": "About PKG UTM Controller", "KR": "PKG UTM Controller 정보"},
    "about.program_info": {"en": "Program Information", "KR": "프로그램 정보"},
    "about.name": {"en": "Name:", "KR": "이름:"},
    "about.version": {"en": "Version:", "KR": "버전:"},
    "about.released": {"en": "Released:", "KR": "출시일:"},
    "about.dev_team": {"en": "Development Team", "KR": "개발팀"},
    "about.laboratory": {"en": "Laboratory:", "KR": "연구실:"},
    "about.developer": {"en": "Developer:", "KR": "개발자:"},
    "about.contact": {"en": "Contact:", "KR": "연락처:"},
    "about.close": {"en": "Close", "KR": "닫기"},
    "about.copyright": {
        "en": "© 2025 [PKG]. All rights reserved.\nFor research and educational purposes.",
        "KR": "© 2025 [PKG]. 모든 권리 보유.\n연구 및 교육 목적으로 사용됩니다."
    },
    # ===== 에러 메시지 =====
    "error.not_connected": {"en": "Device Not Connected", "KR": "장치 미연결"},
    "error.not_connected_desc": {
        "en": "{0} is not connected.\nPlease connect the device first.",
        "KR": "{0}이(가) 연결되지 않았습니다.\n먼저 장치를 연결하세요."
    },
    
    "error.connection_failed": {"en": "Connection Failed", "KR": "연결 실패"},
    "error.connection_failed_desc": {
        "en": "{0} connection failed.\nPort: {1}\nError: {2}\n\nPlease check:\n• Device connection\n• Correct port\n• Other programs using the port",
        "KR": "{0} 연결에 실패했습니다.\n포트: {1}\n오류: {2}\n\n다음 사항을 확인하세요:\n• 장비가 연결되어 있는지\n• 올바른 포트인지\n• 다른 프로그램이 사용 중인지"
    },
    
    "error.communication_error": {"en": "Communication Error", "KR": "통신 오류"},
    "error.communication_error_desc": {
        "en": "Communication error with {0}.\n\nError: {1}\n\nPlease check the connection.",
        "KR": "{0} 통신 중 오류가 발생했습니다.\n\n오류: {1}\n\n연결 상태를 확인하세요."
    },
    
    "error.port_required": {"en": "Port Selection Required", "KR": "포트 선택 필요"},
    "error.select_port": {
        "en": "Please select a port or connect the device.",
        "KR": "포트를 선택하거나 장치를 연결하세요."
    },
    
    "error.input_error": {"en": "Input Error", "KR": "입력 오류"},
    "error.value_error_desc": {
        "en": "{0} value is incorrect.\n\nExpected format: {1}",
        "KR": "{0} 값이 올바르지 않습니다.\n\n예상 형식: {1}"
    },
    
    # ===== 성공 메시지 =====
    "success.connected": {"en": "Connection Successful", "KR": "연결 성공"},
    "success.connected_desc": {
        "en": "{0} connected successfully.\nPort: {1}",
        "KR": "{0} 연결에 성공했습니다.\n포트: {1}"
    },
    
    "success.disconnected": {"en": "Disconnected", "KR": "연결 해제"},
    "success.disconnected_desc": {
        "en": "{0} has been disconnected.",
        "KR": "{0} 연결이 해제되었습니다."
    },
    
    "success.service_failed": {"en": "Service Failed", "KR": "서비스 실패"},
    "success.service_failed_desc": {
        "en": "{0} service failed to start.",
        "KR": "{0} 서비스 시작 실패."
    },
    
    # ===== 일반 메시지 =====
    "msg.frequency_set": {"en": "Frequency Set", "KR": "주파수 설정"},
    "msg.frequency_set_desc": {
        "en": "Monitoring frequency set to {0} Hz ({1} ms).",
        "KR": "모니터링 주파수가 {0} Hz ({1} ms)로 설정되었습니다."
    },
    
    "msg.frequency_positive": {
        "en": "Frequency must be greater than 0.",
        "KR": "주파수는 0보다 커야 합니다."
    },
    
    "msg.reset": {"en": "Reset", "KR": "리셋"},
    "msg.reset_desc": {
        "en": "Motor will return to origin (0).",
        "KR": "모터가 원점(0)으로 이동합니다."
    },
    
    "msg.reset_warning": {"en": "Reset Warning", "KR": "리셋 경고"},
    "msg.reset_warning_desc": {
        "en": "Motor not connected. Movement skipped.",
        "KR": "모터가 연결되지 않아 이동은 생략합니다."
    },
    
    "msg.move_command_failed": {
        "en": "Motor move command failed (communication error).",
        "KR": "모터 이동 명령 실패 (통신 오류)."
    },
    
    "msg.pretension_error": {"en": "Error", "KR": "오류"},
    "msg.pretension_error_desc": {
        "en": "Motor not connected or Pretension feature unavailable.",
        "KR": "모터가 연결되지 않았거나 Pretension 기능이 준비되지 않았습니다."
    },
    
    "msg.pretension_complete": {"en": "Complete", "KR": "완료"},
    "msg.pretension_complete_desc": {
        "en": "Initial load setup and motor zero point configuration completed.",
        "KR": "초기 하중 설정 및 모터 0점 설정 완료."
    },
    
    "msg.file_error": {"en": "File Error", "KR": "파일 오류"},
    "msg.log_file_error_desc": {
        "en": "Cannot start log file:\n{0}",
        "KR": "로그 파일을 시작할 수 없습니다:\n{0}"
    },
    
    "msg.zeroing_error": {"en": "Zeroing Error", "KR": "영점 설정 오류"},
    "msg.zeroing_failed_desc": {
        "en": "Zeroing failed: {0}",
        "KR": "Zeroing 실패: {0}"
    },
        "error.unknown_error": {
        "en": "An unknown error occurred.",
        "KR": "알 수 없는 오류가 발생했습니다."
    },
    
    "error.permission_denied": {
        "en": "Port access permission denied.\nAnother program may be using it or administrator rights may be required.",
        "KR": "포트 접근 권한이 없습니다.\n다른 프로그램이 사용 중이거나 관리자 권한이 필요할 수 있습니다."
    },
    
    "error.port_open_failed": {
        "en": "Could not open port.\nIt may be in use by another program.",
        "KR": "포트를 열 수 없습니다.\n다른 프로그램에서 사용 중일 수 있습니다."
    },
    
    "error.device_timeout": {
        "en": "Device not responding.\nPlease check power and cable connection.",
        "KR": "장비가 응답하지 않습니다.\n전원과 케이블 연결을 확인하세요."
    },
    
    "error.modbus_error": {
        "en": "Communication error occurred.\nPlease check port settings.",
        "KR": "통신 오류가 발생했습니다.\n포트 설정을 확인하세요."
    },
    
    "error.protocol_error": {
        "en": "Wrong device or incorrect communication settings.\nPlease check port selection.",
        "KR": "올바른 장비가 아니거나 통신 설정이 잘못되었습니다.\n포트 선택을 다시 확인하세요."
    },
    
    "error.parsing_error": {
        "en": "Received invalid data from device.\nPlease check cable connection.",
        "KR": "장비로부터 잘못된 데이터를 받았습니다.\n케이블 연결을 확인하세요."
    },
    
    "error.program_error": {
        "en": "Program error occurred.\nPlease restart the program or contact administrator.",
        "KR": "프로그램 오류가 발생했습니다.\n프로그램을 재시작하거나 관리자에게 문의하세요."
    },
    
    "error.port_not_found": {
        "en": "Selected port does not exist.\nPlease check device connection and refresh ports.",
        "KR": "선택한 포트가 존재하지 않습니다.\n장비 연결을 확인하고 포트를 새로고침하세요."
    },
    
    "error.connection_generic": {
        "en": "Connection error occurred.\nPlease check device and port settings.",
        "KR": "연결 오류가 발생했습니다.\n장비와 포트 설정을 확인하세요."
    },

    # ===== 온도 제어 메시지 =====
    "temp.control_started": {"en": "Control Started", "KR": "제어 시작"},
    "temp.control_started_desc": {
        "en": "CH{0} temperature control started\n\nTarget: {1}°C\nAuto Tuning: {2}",
        "KR": "CH{0} 온도 제어 시작\n\n목표 온도: {1}°C\n오토튜닝: {2}"
    },
    "temp.at_running": {"en": "Running", "KR": "실행"},
    "temp.at_stopped": {"en": "Stopped", "KR": "정지"},

    "temp.control_failed": {"en": "Control Failed", "KR": "제어 실패"},
    "temp.control_failed_desc": {
        "en": "Failed to start temperature control.",
        "KR": "온도 제어 시작 실패."
    },

    "temp.control_stopped": {"en": "Control Stopped", "KR": "제어 정지"},
    "temp.control_stopped_desc": {
        "en": "Temperature control has been stopped.",
        "KR": "온도 제어가 정지되었습니다."
    },

    "temp.stabilization_complete": {"en": "Stabilization Complete", "KR": "안정화 완료"},
    "temp.stabilization_complete_desc": {
        "en": " Temperature stabilization achieved!\n\nTarget: {0:.1f}°C ±{1:.1f}°C\nDuration: {2:.1f} min",
        "KR": " 온도 안정화 완료!\n\n목표: {0:.1f}°C ±{1:.1f}°C\n유지: {2:.1f}분"
    },
    # ===== 시간 스케일 =====
    "temp.auto_scale": {
        "en": "Auto Scale (uncheck for manual zoom/pan)", 
        "KR": "자동 스케일 (해제 시 마우스로 자유 조작)"
    },
    "temp.auto_scale_tooltip": {
        "en": "Check: Auto-scroll to show recent 60 seconds\nUncheck: Free zoom/pan with mouse\nRight-click graph → 'View All' to see all data",
        "KR": "체크: 최근 60초 자동 스크롤\n해제: 마우스로 자유롭게 확대/이동\n그래프 우클릭 → 'View All'로 전체 보기"
    },
}