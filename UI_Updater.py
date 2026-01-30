# UI_Updater.py
"""
UI 업데이트 전담
"""

import logging
from interfaces import IUIUpdater

logger = logging.getLogger(__name__)


class UIUpdater(IUIUpdater):
    """
    GUI 라벨 업데이트
    
    책임:
    - UI 위젯에 값 표시
    - 포맷팅 (소수점, 단위 등)
    """
    
    def __init__(self, ui):
        self.ui = ui
        logger.info("UIUpdater 초기화")
    
    def update_motor_position(self, pos_um: float):
        """모터 위치 라벨 업데이트"""
        try:
            # Setting 탭
            if hasattr(self.ui, "En0Positionnow_label"):
                self.ui.En0Positionnow_label.setText(f"{pos_um:.1f} [um]")
            
            # Test 탭
            if hasattr(self.ui, "test_pos_label"):
                self.ui.test_pos_label.setText(f"{pos_um:.1f} [um]")
        
        except Exception as e:
            logger.error(f"모터 위치 UI 업데이트 실패: {e}")
    
    def update_loadcell_value(self, force_n: float):
        """로드셀 값 라벨 업데이트"""
        try:
            # Setting 탭
            if hasattr(self.ui, "Load0Currentnow_label"):
                self.ui.Load0Currentnow_label.setText(f"{force_n:.3f} [N]")
            
            # Test 탭
            if hasattr(self.ui, "test_load_label"):
                self.ui.test_load_label.setText(f"{force_n:.3f} [N]")
        
        except Exception as e:
            logger.error(f"로드셀 UI 업데이트 실패: {e}")
    
    def update_temperature(self, channel: int, temp: float):
        """온도 라벨 업데이트"""
        try:
            if hasattr(self.ui, 'temp_channels') and channel in self.ui.temp_channels:
                self.ui.temp_channels[channel]['lbl'].setText(f"{temp:.1f} °C")
        
        except Exception as e:
            logger.error(f"온도 UI 업데이트 실패 (CH{channel}): {e}")