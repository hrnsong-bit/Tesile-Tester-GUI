# FontManager.py
import logging
from PyQt5 import QtWidgets, QtGui
from Settings_Manager import SettingsManager

logger = logging.getLogger(__name__)

class FontManager:
    """
    애플리케이션 전체 폰트 크기를 관리하는 클래스
    """
    
    # 폰트 크기 프리셋
    FONT_SIZES = {
        "Small": 10,
        "Medium": 12,
        "Large": 14,
        "Extra Large": 16
    }
    
    def __init__(self, app: QtWidgets.QApplication):
        """
        Args:
            app: QApplication 인스턴스
        """
        self.app = app
        self.settings_mgr = SettingsManager()
        self.current_size_name = "Medium"  # 기본값
        
        # 저장된 폰트 크기 불러오기
        self._load_saved_font_size()
        
    def _load_saved_font_size(self):
        """저장된 폰트 크기 불러오기"""
        try:
            saved_size = self.settings_mgr.load_font_size()
            
            # 저장된 크기가 프리셋에 있는지 확인
            for name, size in self.FONT_SIZES.items():
                if size == saved_size:
                    self.current_size_name = name
                    break
            
            logger.info(f"저장된 폰트 크기 복원: {self.current_size_name} ({saved_size}pt)")
            self.apply_font_size(self.current_size_name)
            
        except Exception as e:
            logger.warning(f"폰트 크기 불러오기 실패: {e}, 기본값 사용")
            self.apply_font_size("Medium")
    
    def apply_font_size(self, size_name: str) -> bool:
        """
        폰트 크기 적용
        
        Args:
            size_name: "Small", "Medium", "Large", "Extra Large"
            
        Returns:
            bool: 성공 여부
        """
        if size_name not in self.FONT_SIZES:
            logger.error(f"잘못된 폰트 크기: {size_name}")
            return False
        
        try:
            size = self.FONT_SIZES[size_name]
            
            # 현재 폰트 가져오기
            current_font = self.app.font()
            
            # 새 폰트 생성 (기존 폰트 패밀리 유지)
            new_font = QtGui.QFont(current_font.family(), size, current_font.weight())
            
            # 애플리케이션 전체에 적용
            self.app.setFont(new_font)
            
            # 현재 크기 업데이트
            self.current_size_name = size_name
            
            # 설정 저장
            self.settings_mgr.save_font_size(size)
            
            logger.info(f"폰트 크기 변경: {size_name} ({size}pt)")
            return True
            
        except Exception as e:
            logger.error(f"폰트 크기 적용 실패: {e}")
            return False
    
    def get_current_size_name(self) -> str:
        """현재 폰트 크기 이름 반환"""
        return self.current_size_name
    
    def get_current_size_pt(self) -> int:
        """현재 폰트 크기(pt) 반환"""
        return self.FONT_SIZES[self.current_size_name]
    
    def create_font_menu(self, parent_menu: QtWidgets.QMenu) -> None:
        """
        폰트 크기 서브메뉴 생성
        
        Args:
            parent_menu: 부모 메뉴
        """
        font_menu = parent_menu.addMenu("🔤 Font Size")
        
        # 액션 그룹 (라디오 버튼처럼 하나만 선택)
        action_group = QtWidgets.QActionGroup(parent_menu)
        action_group.setExclusive(True)
        
        for size_name in self.FONT_SIZES.keys():
            action = QtWidgets.QAction(size_name, parent_menu)
            action.setCheckable(True)
            
            # 현재 크기면 체크
            if size_name == self.current_size_name:
                action.setChecked(True)
            
            # 람다 함수로 크기 이름 전달
            action.triggered.connect(
                lambda checked, name=size_name: self.apply_font_size(name)
            )
            
            action_group.addAction(action)
            font_menu.addAction(action)
        
        logger.debug("폰트 크기 메뉴 생성 완료")
