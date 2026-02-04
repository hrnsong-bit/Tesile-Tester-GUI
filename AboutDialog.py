# AboutDialog.py
import logging
from PyQt5 import QtWidgets, QtCore, QtGui

logger = logging.getLogger(__name__)

class AboutDialog(QtWidgets.QDialog):
    """
    About 다이얼로그 (다국어 지원)
    """
    
    def __init__(self, parent=None, language_manager=None):
        super().__init__(parent)
        self.lang_mgr = language_manager
        self.setModal(True)
        
        self._setup_ui()
        self.retranslate_ui()
        
    def _setup_ui(self):
        """UI 구성"""
        self.setFixedSize(400, 500)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 로고 영역
        logo_frame = QtWidgets.QFrame()
        logo_frame.setFrameShape(QtWidgets.QFrame.Box)
        logo_frame.setFixedHeight(150)
        logo_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 2px solid #cccccc;
                border-radius: 8px;
            }
        """)
        
        logo_layout = QtWidgets.QVBoxLayout(logo_frame)
        logo_layout.setAlignment(QtCore.Qt.AlignCenter)
        
        self.logo_placeholder = QtWidgets.QLabel("🔬")
        self.logo_placeholder.setAlignment(QtCore.Qt.AlignCenter)
        self.logo_placeholder.setStyleSheet("font-size: 72pt; border: none;")
        logo_layout.addWidget(self.logo_placeholder)
        
        self.lab_name_label = QtWidgets.QLabel("PKG")
        self.lab_name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.lab_name_label.setStyleSheet("font-size: 14pt; font-weight: bold; border: none;")
        logo_layout.addWidget(self.lab_name_label)
        
        layout.addWidget(logo_frame)
        
        # 프로그램 정보
        self.info_group = QtWidgets.QGroupBox()
        info_layout = QtWidgets.QFormLayout(self.info_group)
        info_layout.setLabelAlignment(QtCore.Qt.AlignRight)
        info_layout.setSpacing(10)
        
        self.name_label_txt = QtWidgets.QLabel()
        self.name_label = QtWidgets.QLabel("UTM Control System")
        self.name_label.setStyleSheet("font-weight: bold;")
        info_layout.addRow(self.name_label_txt, self.name_label)
        
        self.version_label_txt = QtWidgets.QLabel()
        self.version_label = QtWidgets.QLabel("1.0.0")
        info_layout.addRow(self.version_label_txt, self.version_label)
        
        self.date_label_txt = QtWidgets.QLabel()
        self.date_label = QtWidgets.QLabel("2026")
        info_layout.addRow(self.date_label_txt, self.date_label)
        
        layout.addWidget(self.info_group)
        
        # 개발자 정보
        self.dev_group = QtWidgets.QGroupBox()
        dev_layout = QtWidgets.QVBoxLayout(self.dev_group)
        dev_layout.setSpacing(8)
        
        self.lab_label = QtWidgets.QLabel()
        self.lab_label.setStyleSheet("font-weight: bold;")
        dev_layout.addWidget(self.lab_label)
        
        self.developer_label = QtWidgets.QLabel("Developer: Lee Jun Young")
        dev_layout.addWidget(self.developer_label)
        
        self.email_label = QtWidgets.QLabel("Contact: jion0308@mju.ac.kr")
        dev_layout.addWidget(self.email_label)
        
        layout.addWidget(self.dev_group)
        
        # 저작권
        self.copyright_label = QtWidgets.QLabel()
        self.copyright_label.setAlignment(QtCore.Qt.AlignCenter)
        self.copyright_label.setStyleSheet("""
            color: #666666;
            font-size: 9pt;
            padding: 10px;
        """)
        self.copyright_label.setWordWrap(True)
        layout.addWidget(self.copyright_label)
        
        layout.addStretch()
        
        # 닫기 버튼
        self.close_btn = QtWidgets.QPushButton()
        self.close_btn.setFixedSize(100, 35)
        self.close_btn.clicked.connect(self.accept)
        
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def retranslate_ui(self):
        """텍스트 번역 적용"""
        if not self.lang_mgr:
            return
        
        tr = self.lang_mgr.translate
        
        self.setWindowTitle(tr("about.title"))
        self.info_group.setTitle(tr("about.program_info"))
        self.name_label_txt.setText(tr("about.name"))
        self.version_label_txt.setText(tr("about.version"))
        self.date_label_txt.setText(tr("about.released"))
        
        self.dev_group.setTitle(tr("about.dev_team"))
        self.lab_label.setText(f"{tr('about.laboratory')} PKG")
        self.developer_label.setText(f"{tr('about.developer')} Lee Jun Young")
        self.email_label.setText(f"{tr('about.contact')} jion0308@mju.ac.kr")
        
        self.copyright_label.setText(tr("about.copyright"))
        self.close_btn.setText(tr("about.close"))
    
    def set_logo_image(self, image_path: str):
        """로고 이미지 설정"""
        try:
            pixmap = QtGui.QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    120, 120,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation
                )
                self.logo_placeholder.setPixmap(scaled_pixmap)
                self.logo_placeholder.setText("")
        except Exception as e:
            logger.error(f"로고 이미지 설정 실패: {e}")
