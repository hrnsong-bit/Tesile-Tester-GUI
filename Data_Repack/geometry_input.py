"""
시편 치수 입력 위젯 (프리셋 저장/불러오기)
"""

import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QPushButton, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt

from .utils import font_big, PRESET_FILE


class GeometryInput(QWidget):
    """시편 치수 입력 위젯"""
    
    def __init__(self, w="3.8", t="0.08", L0="50"):
        super().__init__()
        f = font_big()
        self.presets = {}

        self.w = QLineEdit(w)
        self.w.setFont(f)
        self.w.setFixedWidth(80)
        
        self.t = QLineEdit(t)
        self.t.setFont(f)
        self.t.setFixedWidth(80)
        
        self.L0 = QLineEdit(L0)
        self.L0.setFont(f)
        self.L0.setFixedWidth(80)
        
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        row.addWidget(QLabel("Width [mm]"))
        row.addWidget(self.w)
        row.addWidget(QLabel("Thickness [mm]"))
        row.addWidget(self.t)
        row.addWidget(QLabel("Gauge [mm]"))
        row.addWidget(self.L0)
        row.addStretch(1)

        preset_row = QHBoxLayout()
        preset_row.setContentsMargins(0, 5, 0, 0)
        
        self.cmb_presets = QComboBox()
        self.cmb_presets.setFont(f)
        self.cmb_presets.setPlaceholderText("--- Select Preset ---")
        
        self.btn_save_preset = QPushButton("Save")
        self.btn_save_preset.setFont(f)
        self.btn_del_preset = QPushButton("Del")
        self.btn_del_preset.setFont(f)
        
        preset_row.addWidget(QLabel("Preset:"))
        preset_row.addWidget(self.cmb_presets, 1)
        preset_row.addWidget(self.btn_save_preset)
        preset_row.addWidget(self.btn_del_preset)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        main_layout.addLayout(row)
        main_layout.addLayout(preset_row)

        self._load_presets()
        self.cmb_presets.activated.connect(self._apply_preset)
        self.btn_save_preset.clicked.connect(self._save_preset)
        self.btn_del_preset.clicked.connect(self._delete_preset)

    def get(self): 
        """현재 입력된 치수 반환"""
        try:
            w_val = float(self.w.text())
            t_val = float(self.t.text())
            L0_val = float(self.L0.text())
            return w_val, t_val, L0_val
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", f"숫자 변환 실패: {e}\n유효한 숫자를 입력하세요.")
            raise ValueError(f"입력값 오류: {e}")

    def _load_presets(self):
        """프리셋 파일에서 불러오기"""
        self.cmb_presets.blockSignals(True)
        self.cmb_presets.clear()
        
        if PRESET_FILE.exists():
            try:
                with open(PRESET_FILE, 'r', encoding='utf-8') as f:
                    self.presets = json.load(f)
            except Exception:
                self.presets = {}
        else:
            self.presets = {}
        
        if self.presets:
            self.cmb_presets.addItems(sorted(self.presets.keys()))
        
        self.cmb_presets.setCurrentIndex(-1)
        self.cmb_presets.blockSignals(False)

    def _apply_preset(self, index):
        """선택한 프리셋 적용"""
        name = self.cmb_presets.itemText(index)
        if name in self.presets:
            data = self.presets[name]
            self.w.setText(data.get("w", "0"))
            self.t.setText(data.get("t", "0"))
            self.L0.setText(data.get("L0", "0"))
            
    def _save_preset(self):
        """현재 값을 프리셋으로 저장"""
        try:
            current_w, current_t, current_L0 = self.get()
        except ValueError:
            return

        name, ok = QInputDialog.getText(self, "Save Preset", "Enter preset name:")
        
        if ok and name:
            self.presets[name] = {
                "w": str(current_w), 
                "t": str(current_t), 
                "L0": str(current_L0)
            }
            self._save_to_file()
            self._load_presets()
            self.cmb_presets.setCurrentText(name)
    
    def _delete_preset(self):
        """선택한 프리셋 삭제"""
        name = self.cmb_presets.currentText()
        if not name or name not in self.presets:
            QMessageBox.warning(self, "Error", "삭제할 프리셋이 선택되지 않았습니다.")
            return

        reply = QMessageBox.question(
            self, 
            "Delete Preset",
            f"정말 '{name}' 프리셋을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if name in self.presets:
                del self.presets[name]
                self._save_to_file()
                self._load_presets()

    def _save_to_file(self):
        """프리셋을 파일에 저장"""
        try:
            with open(PRESET_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"프리셋 저장 실패: {e}")
