"""
CSV Preprocessor Tab
CSV 전처리 도구 (시작점 설정, 범위 삭제 등)
"""

import os
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QComboBox, QPushButton, QFileDialog, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector

from .utils import safe_read_csv, font_big, font_small, SK_GRAY, SK_ORANGE, SK_BLUE


class TabPreprocessor(QWidget):
    """CSV Preprocessor Tab"""
    
    def __init__(self, lang_manager=None):
        super().__init__()
        
        # ===== LanguageManager 저장 =====
        self.lang_manager = lang_manager
        
        f = font_big()
        self.df_original = None
        self.df_processed = None
        self.selector = None
        
        self.clicked_point_marker = None
        self.clicked_point_coords = None
        self.selected_range = None

        self._pan_info = {}
        self._click_info = {}

        # ===== Control Panel =====
        self.ctrl = QGroupBox("CSV Preprocessor")
        self.ctrl.setFont(f)
        gl = QVBoxLayout(self.ctrl)

        # 파일 로드
        file_row = QHBoxLayout()
        self.btn = QPushButton("Load CSV")
        self.btn.setFont(f)
        self.btn.clicked.connect(self.load_csv)
        self.lbl = QLabel("File: -")
        file_row.addWidget(self.btn)
        file_row.addWidget(self.lbl, 1)
        gl.addLayout(file_row)

        # 컬럼 선택
        col_row = QHBoxLayout()
        self.x_col_label = QLabel("X column:") 
        col_row.addWidget(self.x_col_label)
        self.cmb_eps = QComboBox()
        self.cmb_eps.setFont(f)
        col_row.addWidget(self.cmb_eps)
        
        self.y_col_label = QLabel("Y column:")
        col_row.addWidget(self.y_col_label)
        self.cmb_sig = QComboBox()
        self.cmb_sig.setFont(f)
        col_row.addWidget(self.cmb_sig)
        gl.addLayout(col_row)

        self.cmb_eps.currentTextChanged.connect(self.plot_full)
        self.cmb_sig.currentTextChanged.connect(self.plot_full)

        # Info
        self.lbl_info = QLabel("Ready. Load a CSV file.")
        self.lbl_info.setFont(font_small())
        gl.addWidget(self.lbl_info)

        # Buttons
        btn_row1 = QHBoxLayout()
        self.btn_set_start = QPushButton("Set as Start")
        self.btn_set_start.setFont(f)
        self.btn_set_start.clicked.connect(self.set_start_point)
        btn_row1.addWidget(self.btn_set_start)

        self.btn_reset = QPushButton("Reset Data")
        self.btn_reset.setFont(f)
        self.btn_reset.clicked.connect(self.reset_data)
        btn_row1.addWidget(self.btn_reset)
        gl.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        self.btn_del_in = QPushButton("Delete Inside Range")
        self.btn_del_in.setFont(f)
        self.btn_del_in.clicked.connect(self.delete_inside)
        btn_row2.addWidget(self.btn_del_in)

        self.btn_del_out = QPushButton("Delete Outside Range (Crop)")
        self.btn_del_out.setFont(f)
        self.btn_del_out.clicked.connect(self.delete_outside)
        btn_row2.addWidget(self.btn_del_out)
        gl.addLayout(btn_row2)
        
        self.btn_export = QPushButton("Export Processed CSV")
        self.btn_export.setFont(f)
        self.btn_export.clicked.connect(self.export_csv)
        gl.addWidget(self.btn_export)

        # ===== Graph =====
        fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = fig.add_subplot(111)
        self.canvas = FigureCanvas(fig)
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)

        # ===== Layout =====
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)
        root.addWidget(self.ctrl, stretch=0)
        root.addWidget(self.toolbar, stretch=0)
        root.addWidget(self.canvas, stretch=1)

    def load_csv(self):
        """CSV 파일 로드"""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select CSV", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        if not path: 
            return
        try:
            df = safe_read_csv(path)
            df.columns = [c.strip() for c in df.columns]
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read CSV:\n{e}")
            return
            
        self.df_original = df
        self.df_processed = df.copy()
        
        self.lbl.setText(f"File: {os.path.basename(path)}")
        cols = df.columns.tolist()
        
        self.cmb_eps.blockSignals(True)
        self.cmb_sig.blockSignals(True)
        self.cmb_eps.clear()
        self.cmb_sig.clear()
        for c in cols:
            self.cmb_eps.addItem(c)
            self.cmb_sig.addItem(c)
        
        if len(cols) > 0:
            self.cmb_eps.setCurrentIndex(0)
        if len(cols) > 1:
            self.cmb_sig.setCurrentIndex(1)
        
        self.cmb_eps.blockSignals(False)
        self.cmb_sig.blockSignals(False)

        self.plot_full() 
        self.lbl_info.setText(f"Loaded {len(df)} data points.")

    def plot_full(self):
        """전체 데이터 플롯 (원본 + 편집본)"""
        if self.df_processed is None or self.df_original is None: 
            return
            
        x_col_name = self.cmb_eps.currentText().strip()
        y_col_name = self.cmb_sig.currentText().strip()
        if not (x_col_name and y_col_name):
            return

        self.ax.clear()
        self.clear_markers()

        self.ax.figure.subplots_adjust(bottom=0.15, left=0.12)

        self.x_col_label.setText(f"{x_col_name}:")
        self.y_col_label.setText(f"{y_col_name}:")

        x_orig = np.asarray(self.df_original[x_col_name], dtype=float)
        y_orig = np.asarray(self.df_original[y_col_name], dtype=float)
        self.ax.plot(
            x_orig, 
            y_orig, 
            color=SK_GRAY, 
            lw=1.0, 
            ls='--', 
            marker='.', 
            markersize=2, 
            label="Original"
        )

        x_proc = np.asarray(self.df_processed[x_col_name], dtype=float)
        y_proc = np.asarray(self.df_processed[y_col_name], dtype=float)
        self.ax.plot(x_proc, y_proc, color=SK_ORANGE, lw=1.8, label="Processed")

        self.ax.set_xlabel(x_col_name)
        self.ax.set_ylabel(y_col_name)
        
        self.ax.grid(True, ls="--", alpha=0.4)
        self.ax.legend()
        
        self._pan_info = {}
        self._click_info = {}
        self.selected_range = None

        self.canvas.draw_idle()

        self._init_span_selector(self.ax)

    def clear_markers(self):
        """클릭 포인트 마커 제거"""
        if self.clicked_point_marker:
            try: 
                self.clicked_point_marker.remove()
            except Exception: 
                pass
            self.clicked_point_marker = None
        self.clicked_point_coords = None

    def _init_span_selector(self, ax):
        """SpanSelector 초기화 (범위 선택용)"""
        if self.selector is not None:
            try: 
                self.selector.disconnect_events()
            except Exception: 
                pass
            self.selector = None
        
        self.selector = SpanSelector(
            ax, 
            self._on_select, 
            "horizontal",
            minspan=0.0001, 
            useblit=True,
            props=dict(facecolor=SK_BLUE, alpha=0.22, edgecolor=SK_BLUE),
            interactive=True, 
            drag_from_anywhere=True,
            button=1 
        )
        self.canvas.draw_idle()

    def _set_click_point(self, x_val, y_val):
        """클릭한 지점을 시작점으로 설정"""
        if x_val is None or y_val is None:
            return
            
        if self.clicked_point_marker:
            try: 
                self.clicked_point_marker.remove()
            except Exception: 
                pass
        
        self.clicked_point_marker = self.ax.plot(
            x_val, 
            y_val, 
            'x', 
            color=SK_BLUE, 
            markersize=10, 
            mew=2
        )[0]
        self.canvas.draw_idle()
        
        self.clicked_point_coords = (x_val, y_val)
        self.lbl_info.setText(f"Start point selected at (X={x_val:.4f}, Y={y_val:.2f})")

    def _on_mouse_press(self, event):
        """마우스 누름 이벤트"""
        if event.inaxes != self.ax or self.toolbar.mode != "":
            return

        if event.button == 1:
            self._click_info = {'x': event.xdata, 'y': event.ydata, 'is_drag': False}
        
        elif event.button == 3:
            self._pan_info = {
                'active': True,
                'start_x': event.x,
                'start_y': event.y,
                'start_xlim': self.ax.get_xlim(),
                'start_ylim': self.ax.get_ylim(),
            }
            if self.selector:
                self.selector.set_active(False)

    def _on_mouse_move(self, event):
        """마우스 이동 이벤트"""
        if event.inaxes != self.ax:
            return
            
        if event.button == 1 and self._click_info.get('x') is not None:
            self._click_info['is_drag'] = True

        elif self._pan_info.get('active'):
            dx = event.x - self._pan_info['start_x']
            dy = event.y - self._pan_info['start_y']

            x1_0, x2_0 = self._pan_info['start_xlim']
            y1_0, y2_0 = self._pan_info['start_ylim']

            pix_x1_0, pix_y1_0 = self.ax.transData.transform((x1_0, y1_0))
            pix_x1_new = pix_x1_0 - dx
            pix_y1_new = pix_y1_0 - dy
            data_x1_new, data_y1_new = self.ax.transData.inverted().transform(
                (pix_x1_new, pix_y1_new)
            )

            data_dx = data_x1_new - x1_0
            data_dy = data_y1_new - y1_0

            self.ax.set_xlim(x1_0 + data_dx, x2_0 + data_dx)
            self.ax.set_ylim(y1_0 + data_dy, y2_0 + data_dy)
            
            self.canvas.draw_idle()

    def _on_mouse_release(self, event):
        """마우스 떼기 이벤트"""
        if event.inaxes != self.ax:
            return

        if event.button == 1:
            if not self._click_info.get('is_drag'):
                self._set_click_point(event.xdata, event.ydata)
            self._click_info = {}
            
        elif event.button == 3:
            self._pan_info = {'active': False}
            if self.selector:
                self.selector.set_active(True)
        
        self.canvas.draw_idle()
    
    def _on_select(self, xmin, xmax):
        """SpanSelector로 범위 선택 완료 시 호출"""
        self.clear_markers() 
        self.selected_range = (xmin, xmax)
        self.lbl_info.setText(f"Range selected from {xmin:.2f} to {xmax:.2f}")

    def set_start_point(self):
        """선택한 지점 이전 데이터 제거"""
        if self.df_processed is None:
            QMessageBox.warning(self, "No Data", "먼저 CSV 파일을 로드하세요.")
            return
        if self.clicked_point_coords is None:
            QMessageBox.warning(
                self, 
                "No Point", 
                "그래프를 클릭하여 시작점을 먼저 선택하세요."
            )
            return

        x_col_name = self.cmb_eps.currentText().strip()
        x_offset, y_offset = self.clicked_point_coords

        df = self.df_original.copy()
        df = df[df[x_col_name] >= x_offset].copy()
        df.reset_index(drop=True, inplace=True)

        self.df_processed = df
        self.plot_full()
        self.lbl_info.setText(
            f"Trimmed data before X={x_offset:.4f}. {len(df)} points remaining."
        )

    def delete_inside(self):
        """선택한 범위 내부 데이터 삭제"""
        if self.df_processed is None:
            QMessageBox.warning(self, "No Data", "먼저 CSV 파일을 로드하세요.")
            return
        if self.selected_range is None:
            QMessageBox.warning(
                self, 
                "No Range", 
                "그래프를 드래그하여 삭제할 범위를 선택하세요."
            )
            return

        x_col_name = self.cmb_eps.currentText().strip()
        min_x = self.selected_range[0]
        max_x = self.selected_range[1]

        df = self.df_processed.copy()
        mask = (df[x_col_name] < min_x) | (df[x_col_name] > max_x)
        self.df_processed = df[mask].copy()
        
        self.plot_full()
        self.lbl_info.setText(
            f"Deleted data inside range. {len(self.df_processed)} points remaining."
        )

    def delete_outside(self):
        """선택한 범위 외부 데이터 삭제 (Crop)"""
        if self.df_processed is None:
            QMessageBox.warning(self, "No Data", "먼저 CSV 파일을 로드하세요.")
            return
        if self.selected_range is None:
            QMessageBox.warning(
                self, 
                "No Range", 
                "그래프를 드래그하여 보존할 범위를 선택하세요."
            )
            return

        x_col_name = self.cmb_eps.currentText().strip()
        min_x = self.selected_range[0]
        max_x = self.selected_range[1]

        df = self.df_processed.copy()
        mask = (df[x_col_name] >= min_x) & (df[x_col_name] <= max_x)
        self.df_processed = df[mask].copy()
        
        self.plot_full()
        self.lbl_info.setText(
            f"Cropped data to range. {len(self.df_processed)} points remaining."
        )

    def reset_data(self):
        """편집본을 원본 상태로 초기화"""
        if self.df_original is None:
            QMessageBox.warning(self, "No Data", "로드된 원본 데이터가 없습니다.")
            return
            
        self.df_processed = self.df_original.copy()
        self.plot_full()
        self.lbl_info.setText("Data reset to original state.")
        
    def export_csv(self):
        """편집된 데이터를 CSV로 내보내기"""
        if self.df_processed is None:
            QMessageBox.warning(self, "No Data", "내보낼 편집 데이터가 없습니다.")
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Processed CSV", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
            
        try:
            self.df_processed.to_csv(path, index=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CSV:\n{e}")
            return
            
        QMessageBox.information(
            self, 
            "Saved", 
            f"Processed CSV saved to:\n{path}"
        )
    
    def retranslate(self):
        """UI 텍스트 번역 업데이트"""
        if not self.lang_manager:
            return
        
        tr = self.lang_manager.translate
        
        # 그룹박스
        self.ctrl.setTitle(tr("data.preprocessor"))
        
        # 버튼
        self.btn.setText(tr("data.load_csv"))
        self.btn_set_start.setText(tr("data.set_start"))
        self.btn_reset.setText(tr("data.reset_data"))
        self.btn_del_in.setText(tr("data.delete_inside"))
        self.btn_del_out.setText(tr("data.delete_outside"))
        self.btn_export.setText(tr("data.export"))
        
        # 라벨
        self.lbl.setText(tr("data.file") + " -")
        self.x_col_label.setText(tr("data.x_column"))
        self.y_col_label.setText(tr("data.y_column"))
