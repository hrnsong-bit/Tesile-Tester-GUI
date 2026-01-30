# Data_Repack.py

import sys, os
import numpy as np
import pandas as pd
import matplotlib as mpl

import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFileDialog, QLabel, QComboBox, QPushButton, QGroupBox, QLineEdit,
    QMessageBox, QDoubleSpinBox, QCheckBox, QSplitter, QSizePolicy, QListWidget,
    QInputDialog
)

from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtCore import Qt

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.widgets import SpanSelector

# ── Colors
SK_RED = "#EA002C"
SK_MULTI = ["#EA002C", "#FBBC05", "#9BCF0A", "#009A93",
            "#0072C6", "#0E306D", "#68217A", "#000000"]

SK_ORANGE = "#F47725"
SK_BLUE = "#00A0E9"
SK_GRAY = "#777777"

# ── Matplotlib style
mpl.rcParams.update({
    "font.size": 13,
    "axes.labelsize": 14,
    "axes.titlesize": 15,
    "legend.fontsize": 12,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "lines.linewidth": 2.2,
    "grid.linestyle": "--",
    "grid.alpha": 0.35,
    "axes.grid": True,
})

# ========== 개선 1: 절대 경로로 프리셋 파일 위치 설정 ==========
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

PRESET_FILE = BASE_DIR / "specimen_presets.json"


# ========== 개선 2: 폰트 존재 여부 확인 함수 개선 ==========
def font_big():
    """큰 폰트 반환 (시스템에 Pretendard가 있으면 사용, 없으면 Arial)"""
    available_families = QFontDatabase().families()
    if "Pretendard" in available_families:
        return QFont("Pretendard", 13, QFont.DemiBold)
    else:
        return QFont("Arial", 13, QFont.Bold)

def font_small():
    """작은 폰트 반환"""
    available_families = QFontDatabase().families()
    if "Pretendard" in available_families:
        f = QFont("Pretendard", 9)
    else:
        f = QFont("Arial", 9)
    f.setWeight(QFont.Normal)
    return f


def safe_read_csv(path, **kw):
    """CSV 읽기 (UTF-8 실패 시 CP949로 재시도)"""
    try:
        return pd.read_csv(path, **kw)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="cp949", **kw)


# ========== 개선 3: 항복 강도 계산 함수에 검증 강화 ==========
def calculate_yield_strength(strain, stress, offset_percent=0.2):
    """
    0.2% 오프셋 방법을 사용하여 항복강도를 계산
    strain: 절대값 (예: 0.01 = 1%)
    stress: MPa
    """
    if len(strain) < 10:
        return None, None, None  # 데이터가 너무 적으면 계산 불가
    
    offset_val = offset_percent / 100.0
    
    # 1. 탄성 영역(Linear Region) 감지 (0.05% ~ 0.25% 구간 사용 가정)
    mask = (strain >= 0.0005) & (strain <= 0.0025)
    
    if np.sum(mask) < 3:
        # 데이터가 너무 적으면 초반 20개 포인트 사용 (Fallback)
        mask = slice(0, min(len(strain), 20))
        
    x_linear = strain[mask]
    y_linear = stress[mask]
    
    if len(x_linear) < 2:
        return None, None, None

    # 1차원 폴리피팅 (y = ax + b) -> 기울기 a가 탄성계수 E
    try:
        slope, intercept = np.polyfit(x_linear, y_linear, 1)
        E_modulus = slope
    except Exception:
        return None, None, None
    
    # 2. 오프셋 라인 생성: y = E * (x - offset)
    offset_line = E_modulus * (strain - offset_val)
    
    # 3. 교차점 찾기 (stress < offset_line 인 지점이 발생하는 순간)
    start_idx = np.argmax(strain > offset_val)
    if start_idx == 0 and strain[0] <= offset_val:
         return None, None, E_modulus

    diff = stress - offset_line
    candidates = np.where(diff[start_idx:] < 0)[0]
    
    if len(candidates) > 0:
        idx_rel = candidates[0]
        yield_idx = start_idx + idx_rel
        yield_strength = stress[yield_idx]
        return yield_strength, yield_idx, E_modulus

    return None, None, E_modulus


class ZoomableCanvas(FigureCanvas):
    """마우스 휠로 줌 가능한 Matplotlib 캔버스"""
    def __init__(self, fig):
        super().__init__(fig)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.mpl_connect('scroll_event', self.on_scroll)

    def on_scroll(self, event):
        if event.inaxes is None: 
            return
        ax = event.inaxes
        base_scale = 1.1
        if event.button == 'up': 
            scale_factor = 1 / base_scale
        elif event.button == 'down': 
            scale_factor = base_scale
        else: 
            return

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        xdata = event.xdata
        ydata = event.ydata
        if xdata is None or ydata is None:
             xdata = (cur_xlim[0] + cur_xlim[1]) / 2
             ydata = (cur_ylim[0] + cur_ylim[1]) / 2

        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        rel_x = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        rel_y = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])

        ax.set_xlim([xdata - new_width * (1-rel_x), xdata + new_width * rel_x])
        ax.set_ylim([ydata - new_height * (1-rel_y), ydata + new_height * rel_y])
        self.draw_idle()


# ── Geometry Input Widget
class GeometryInput(QWidget):
    """시편 치수 입력 위젯 (프리셋 저장/불러오기 기능 포함)"""
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
        """현재 입력된 치수 반환 (w, t, L0)"""
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


# ========== 추가: 컬럼 타입 검증 함수 ==========
def is_likely_strain_column(col_name):
    """컬럼명이 strain 데이터일 가능성이 있는지 확인"""
    col_lower = col_name.lower()
    strain_keywords = ["strain", "ε", "exx", "eyy", "e_", "epsilon", "변형"]
    return any(k in col_lower for k in strain_keywords)

def is_likely_load_column(col_name):
    """컬럼명이 load/force 데이터일 가능성이 있는지 확인"""
    col_lower = col_name.lower()
    load_keywords = ["load", "force", "f_", "하중", "힘"]
    return any(k in col_lower for k in load_keywords)


# ── Tab 1: SS Curve Generator
class TabDICUTM(QWidget):
    """단일 UTM + DIC 파일로부터 응력-변형률 곡선 생성"""
    def __init__(self):
        super().__init__()
        f = font_big()
        self.udf = None
        self.ddf = None
        self.out_df = None
        
        self._pan_info = {}

        ctrl = QGroupBox("Load · Settings")
        ctrl.setFont(f)
        gl = QGridLayout(ctrl)
        gl.setHorizontalSpacing(10)
        gl.setVerticalSpacing(8)

        self.btn_utm = QPushButton("Load UTM CSV")
        self.btn_dic = QPushButton("Load DIC CSV")
        for b in (self.btn_utm, self.btn_dic): 
            b.setFont(f)
        self.btn_utm.clicked.connect(self.load_utm)
        self.btn_dic.clicked.connect(self.load_dic)
        
        self.lbl_utm = QLabel("UTM: -")
        self.lbl_dic = QLabel("DIC: -")
        
        gl.addWidget(self.btn_utm, 0, 0)
        gl.addWidget(self.lbl_utm, 0, 1, 1, 3)
        gl.addWidget(self.btn_dic, 1, 0)
        gl.addWidget(self.lbl_dic, 1, 1, 1, 3)

        gl.addWidget(QLabel("UTM Load (N):"), 2, 0)
        self.cmb_load = QComboBox()
        self.cmb_load.setEnabled(False)
        self.cmb_load.setFont(f)
        gl.addWidget(self.cmb_load, 2, 1)
        
        gl.addWidget(QLabel("DIC Strain (%):"), 2, 2)
        self.cmb_dic = QComboBox()
        self.cmb_dic.setEnabled(False)
        self.cmb_dic.setFont(f)
        gl.addWidget(self.cmb_dic, 2, 3)

        gl.addWidget(QLabel("Merge tol (s):"), 3, 0)
        self.tol = QDoubleSpinBox()
        self.tol.setDecimals(3)
        self.tol.setSingleStep(0.005)
        self.tol.setRange(0.0, 10.0)
        self.tol.setValue(0.06)
        self.tol.setFont(f)
        gl.addWidget(self.tol, 3, 1)
        
        self.chk_yield = QCheckBox("Calc Yield Strength (0.2%)")
        self.chk_yield.setChecked(True)
        gl.addWidget(self.chk_yield, 3, 2, 1, 2)
        
        gl.addWidget(QLabel("Geometry:"), 4, 0)
        self.geom = GeometryInput()
        gl.addWidget(self.geom, 4, 1, 1, 3)

        self.btn_plot = QPushButton("Generate S–S Curve")
        self.btn_plot.setFont(f)
        self.btn_plot.clicked.connect(self.plot_ss)
        
        self.btn_save = QPushButton("Save CSV")
        self.btn_save.setFont(f)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_csv)
        
        self.btn_save_img = QPushButton("Save Graph")
        self.btn_save_img.setFont(f)
        self.btn_save_img.setEnabled(False)
        self.btn_save_img.clicked.connect(self.save_graph)

        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.btn_plot)
        row.addWidget(self.btn_save)
        row.addWidget(self.btn_save_img)
        gl.addLayout(row, 5, 0, 1, 4)

        res = QGroupBox("Results")
        res.setFont(f)
        h = QHBoxLayout(res)
        self.lbl_uts = QLabel("UTS: - (MPa) | YS: - (MPa)")
        h.addWidget(self.lbl_uts)
        h.addStretch(1)

        fig = Figure(figsize=(6, 4), dpi=110)
        self.canvas = ZoomableCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)

        plot_v = QVBoxLayout()
        plot_v.setContentsMargins(0, 0, 0, 0)
        plot_v.addWidget(self.toolbar)
        plot_v.addWidget(self.canvas)
        plot_wrap = QWidget()
        plot_wrap.setLayout(plot_v)

        top = QWidget()
        top_v = QVBoxLayout(top)
        top_v.setContentsMargins(0, 0, 0, 0)
        top_v.setSpacing(8)
        top_v.addWidget(ctrl)
        top_v.addWidget(res)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(top)
        self.splitter.addWidget(plot_wrap)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setSizes([320, 900])

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)
        root.addWidget(self.splitter)
        
        ctrl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        res.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        top.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

    def _on_mouse_press(self, event):
        """우클릭으로 Pan 시작"""
        if self.toolbar.mode != "" or event.inaxes != self.canvas.figure.axes[0]: 
            return
        if event.button == 3:
            ax = self.canvas.figure.axes[0]
            self._pan_info = {
                'active': True, 
                'start_x': event.x, 
                'start_y': event.y, 
                'start_xlim': ax.get_xlim(), 
                'start_ylim': ax.get_ylim()
            }

    def _on_mouse_move(self, event):
        """Pan 중 마우스 이동"""
        if self._pan_info.get('active'):
            ax = self.canvas.figure.axes[0]
            dx = event.x - self._pan_info['start_x']
            dy = event.y - self._pan_info['start_y']
            x1, x2 = self._pan_info['start_xlim']
            y1, y2 = self._pan_info['start_ylim']
            pix_x, pix_y = ax.transData.transform((x1, y1))
            pix_x -= dx
            pix_y -= dy
            new_x, new_y = ax.transData.inverted().transform((pix_x, pix_y))
            ddx = new_x - x1
            ddy = new_y - y1
            ax.set_xlim(x1 + ddx, x2 + ddx)
            ax.set_ylim(y1 + ddy, y2 + ddy)
            self.canvas.draw_idle()

    def _on_mouse_release(self, event):
        """우클릭 해제로 Pan 종료"""
        if event.button == 3: 
            self._pan_info = {'active': False}

    def load_utm(self):
        """UTM CSV 파일 로드"""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select UTM CSV", 
            "", 
            "CSV (*.csv);;All Files (*)"
        )
        if not path: 
            return
        try:
            df = safe_read_csv(path)
            df.columns = [c.strip() for c in df.columns]
            self.udf = df
            self.lbl_utm.setText(f"UTM: {os.path.basename(path)}")
            
            nums = df.select_dtypes(include='number').columns.tolist()
            if nums:
                t0 = df.columns[0]
                others = [c for c in nums if c != t0]
                pref = [c for c in others if ("load" in c.lower() or "force" in c.lower())] or others
                self.cmb_load.clear()
                self.cmb_load.addItems(pref)
                self.cmb_load.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "UTM Load Error", str(e))

    def load_dic(self):
        """DIC CSV 파일 로드"""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select DIC CSV", 
            "", 
            "CSV (*.csv);;All Files (*)"
        )
        if not path: 
            return
        try:
            df = safe_read_csv(path)
            df.columns = [c.strip() for c in df.columns]
            
            time_col = df.columns[0]
            if pd.api.types.is_numeric_dtype(df[time_col]):
                df[time_col] = df[time_col] - df[time_col].iloc[0]

            self.ddf = df
            self.lbl_dic.setText(f"DIC: {os.path.basename(path)}")
            
            nums = df.select_dtypes(include='number').columns.tolist()
            if nums:
                t0 = df.columns[0]
                cand = [c for c in nums if c != t0]
                pri = [c for c in cand if any(k in c.lower() for k in ["strain", "ε", "exx", "eyy", "e_"])]
                self.cmb_dic.clear()
                self.cmb_dic.addItems(pri or cand)
                self.cmb_dic.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "DIC Load Error", str(e))

    def plot_ss(self):
        """응력-변형률 곡선 생성"""
        try:
            self.out_df = None
            self.btn_save.setEnabled(False)
            self.btn_save_img.setEnabled(False)
            
            if self.udf is None or self.ddf is None:
                QMessageBox.warning(self, "Error", "Load both UTM and DIC files.")
                return
            if not (self.cmb_load.isEnabled() and self.cmb_dic.isEnabled()):
                QMessageBox.warning(self, "Error", "Select UTM load and DIC strain columns.")
                return

            # ========== 추가: 컬럼 선택 검증 ==========
            lc = self.cmb_load.currentText()
            sx = self.cmb_dic.currentText()
            
            # UTM에서 strain 선택 경고
            if is_likely_strain_column(lc):
                reply = QMessageBox.warning(
                    self,
                    "Wrong Column Warning",
                    f"⚠️ You selected '{lc}' from UTM file.\n"
                    f"This looks like a STRAIN column, but you should select LOAD/FORCE.\n\n"
                    f"Continue anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # DIC에서 load 선택 경고
            if is_likely_load_column(sx):
                reply = QMessageBox.warning(
                    self,
                    "Wrong Column Warning",
                    f"⚠️ You selected '{sx}' from DIC file.\n"
                    f"This looks like a LOAD/FORCE column, but you should select STRAIN.\n\n"
                    f"Continue anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            try:
                w_mm, t_mm, _ = self.geom.get()
                if w_mm * t_mm == 0:
                    QMessageBox.warning(self, "Error", "Geometry(면적)는 0이 될 수 없습니다.")
                    return
                A = (w_mm * 1e-3) * (t_mm * 1e-3)
            except ValueError:
                return

            tu, td = self.udf.columns[0], self.ddf.columns[0]

            udf = self.udf.sort_values(tu)
            ddf = self.ddf.sort_values(td)
            
            m = pd.merge_asof(
                udf[[tu, lc]], 
                ddf[[td, sx]], 
                left_on=tu, 
                right_on=td,
                direction="nearest", 
                tolerance=self.tol.value()
            ).dropna(subset=[sx])

            if m.empty:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    "Merge result is empty. Check:\n"
                    "1. Time column alignment\n"
                    "2. Tolerance value\n"
                    "3. Data overlap"
                )
                return
            
            if len(m) < 10:
                reply = QMessageBox.question(
                    self,
                    "Warning",
                    f"Only {len(m)} points merged. Results may be unreliable.\n"
                    "Continue anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            eps_eng = m[sx].astype(float) / 100.0
            eps_true = np.log1p(eps_eng)
            sig_eng = (m[lc] - m[lc].iloc[0]) / A / 1e6
            sig_true = sig_eng * (1.0 + eps_eng)

            eps_plot = (eps_true - eps_true.iloc[0]).values
            sig_plot = (sig_true - sig_true.iloc[0]).values

            fig = self.canvas.figure
            fig.clear()
            fig.subplots_adjust(top=1.0, bottom=0.2)
            
            ax = fig.add_subplot(111)
            ax.plot(eps_plot * 100.0, sig_plot, '-', color=SK_RED, label="True σ–ε")
            
            uts = float(np.nanmax(sig_plot))
            
            ys_text = ""
            if self.chk_yield.isChecked():
                ys, ys_idx, E_val = calculate_yield_strength(eps_plot, sig_plot)
                
                if ys is not None:
                    ys_text = f" | YS: {ys:.1f} MPa"
                    ax.plot(
                        eps_plot[ys_idx] * 100.0, 
                        ys, 
                        'o', 
                        color='blue', 
                        label=f"YS: {ys:.1f} MPa"
                    )
                    
                    x_vis = np.linspace(0, eps_plot[ys_idx] * 1.2, 50)
                    y_vis = E_val * (x_vis - 0.002) 
                    ax.plot(
                        x_vis * 100.0, 
                        y_vis, 
                        '--', 
                        color='gray', 
                        alpha=0.5, 
                        label="0.2% Offset"
                    )
                else:
                    ys_text = " | YS: Not Found"
            
            self.lbl_uts.setText(f"UTS: {uts:.1f} MPa{ys_text}")

            ax.set_xlabel("True Strain (%)")
            ax.set_ylabel("True Stress (MPa)")
            ax.legend(loc="upper left", frameon=True)
            self.canvas.draw()

            self.out_df = pd.DataFrame({
                "time_utm_s": m[tu].values, 
                "time_dic_s": m[td].values,
                "load_N": m[lc].values, 
                "dic_percent": m[sx].values,
                "eng_eps": eps_eng.values, 
                "true_eps": eps_true.values,
                "eng_sig_mpa": sig_eng.values, 
                "true_sig_mpa": sig_true.values,
                "true_eps_plot": eps_plot, 
                "true_sig_plot_mpa": sig_plot,
            })
            self.btn_save.setEnabled(True)
            self.btn_save_img.setEnabled(True)

        except Exception as e:
            QMessageBox.warning(self, "Plot Error", str(e))

    def save_csv(self):
        """병합된 데이터를 CSV로 저장"""
        if self.out_df is None or self.out_df.empty:
            QMessageBox.information(self, "Info", "No data to save.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save merged SS CSV", 
            "merged_ss.csv", 
            "CSV (*.csv)"
        )
        if not path: 
            return
        try:
            self.out_df.to_csv(path, index=False, encoding="utf-8-sig")
            QMessageBox.information(self, "Saved", f"Saved:\n{os.path.basename(path)}")
        except Exception as e:
            QMessageBox.warning(self, "Save Error", str(e))

    def save_graph(self):
        """그래프를 이미지로 저장"""
        if self.canvas.figure is None:
            QMessageBox.warning(self, "Error", "No graph to save.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Graph Image", 
            "ss_curve.png", 
            "PNG Image (*.png);;JPEG Image (*.jpg);;PDF Document (*.pdf)"
        )
        if not path:
            return
            
        try:
            self.canvas.figure.savefig(path, dpi=300, bbox_inches='tight')
            QMessageBox.information(
                self, 
                "Saved", 
                f"Graph saved to:\n{os.path.basename(path)}"
            )
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Failed to save graph:\n{e}")


# ── Tab 2: Preprocessor
class TabPreprocessor(QWidget):
    """CSV 전처리 도구 (시작점 설정, 범위 삭제 등)"""
    def __init__(self):
        super().__init__()
        
        f = font_big()
        self.df_original = None
        self.df_processed = None
        self.selector = None
        
        self.clicked_point_marker = None
        self.clicked_point_coords = None
        self.selected_range = None

        self._pan_info = {}
        self._click_info = {}

        ctrl = QGroupBox("CSV Preprocessor")
        ctrl.setFont(f)
        gl = QGridLayout(ctrl)

        self.btn = QPushButton("Load CSV")
        self.btn.setFont(f)
        self.btn.clicked.connect(self.load_csv)
        self.lbl = QLabel("File: -")
        gl.addWidget(self.btn, 0, 0)
        gl.addWidget(self.lbl, 0, 1, 1, 3)

        self.x_col_label = QLabel("X column:") 
        gl.addWidget(self.x_col_label, 1, 0)
        self.cmb_eps = QComboBox()
        self.cmb_eps.setFont(f)
        gl.addWidget(self.cmb_eps, 1, 1)
        
        self.y_col_label = QLabel("Y column:")
        gl.addWidget(self.y_col_label, 1, 2)
        self.cmb_sig = QComboBox()
        self.cmb_sig.setFont(f)
        gl.addWidget(self.cmb_sig, 1, 3)

        self.cmb_eps.currentTextChanged.connect(self.plot_full)
        self.cmb_sig.currentTextChanged.connect(self.plot_full)

        self.lbl_info = QLabel("Ready. Load a CSV file.")
        self.lbl_info.setFont(font_small())
        gl.addWidget(self.lbl_info, 2, 0, 1, 4)

        self.btn_set_start = QPushButton("Set as Start")
        self.btn_set_start.setFont(f)
        self.btn_set_start.clicked.connect(self.set_start_point)
        gl.addWidget(self.btn_set_start, 3, 0, 1, 2)

        self.btn_reset = QPushButton("Reset Data")
        self.btn_reset.setFont(f)
        self.btn_reset.clicked.connect(self.reset_data)
        gl.addWidget(self.btn_reset, 3, 2, 1, 2)

        self.btn_del_in = QPushButton("Delete Inside Range")
        self.btn_del_in.setFont(f)
        self.btn_del_in.clicked.connect(self.delete_inside)
        gl.addWidget(self.btn_del_in, 4, 0, 1, 2)

        self.btn_del_out = QPushButton("Delete Outside Range (Crop)")
        self.btn_del_out.setFont(f)
        self.btn_del_out.clicked.connect(self.delete_outside)
        gl.addWidget(self.btn_del_out, 4, 2, 1, 2)
        
        self.btn_export = QPushButton("Export Processed CSV")
        self.btn_export.setFont(f)
        self.btn_export.clicked.connect(self.export_csv)
        gl.addWidget(self.btn_export, 5, 0, 1, 4)

        fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = fig.add_subplot(111)
        self.canvas = ZoomableCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)
        root.addWidget(ctrl, stretch=0)
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


# ── Tab 3: Multi Compare (개선된 네이밍 로직 + 파일 검증)
class TabMultiCompare(QWidget):
    """
    여러 UTM+DIC 쌍을 비교하는 탭
    - 개선된 네이밍: 수동 추가 방식처럼 공통 접두사 추출
    - 중복 라벨 방지 (동일 라벨 자동 증분)
    - 동일 파일 선택 방지
    """
    SK_COLORS = SK_MULTI
    
    def __init__(self):
        super().__init__()

        f = font_big()
        self.utm_files = []
        self.dic_files = []
        self.pairs = []
        self.datasets = []
        self.selector = None
        self.span = None
        self.vlines = []
        self.ax_info = None
        self._pan_info = {}

        ctrl = QGroupBox("Multi compare · Load & Settings")
        ctrl.setFont(f)
        gl = QGridLayout(ctrl)

        self.btn_load_multi = QPushButton("Load Multiple UTM + DIC")
        self.btn_load_multi.setToolTip("Select UTM files (multi) → then DIC files (multi)")
        self.btn_load_multi.clicked.connect(self.load_multiple_sets)
        gl.addWidget(self.btn_load_multi, 0, 0, 1, 2)

        self.lbl_summary = QLabel("UTM: 0, DIC: 0, Pairs: 0")
        gl.addWidget(self.lbl_summary, 0, 2, 1, 2)
        
        pair_label = QLabel("Pairs (label = auto-extracted):")
        gl.addWidget(pair_label, 1, 0, 1, 2)

        edit_btn_layout = QHBoxLayout()
        edit_btn_layout.setSpacing(5)
        
        self.btn_add_single = QPushButton("Add")
        self.btn_add_single.setToolTip("Add one UTM + DIC pair manually")
        self.btn_add_single.clicked.connect(self._add_single_pair)
        
        self.btn_edit_label = QPushButton("Edit Label")
        self.btn_edit_label.clicked.connect(self._edit_selected_label)
        self.btn_edit_label.setToolTip("Edit the label of selected pair")
        
        self.btn_remove_pair = QPushButton("Remove")
        self.btn_remove_pair.clicked.connect(self._remove_selected_pair)
        self.btn_remove_pair.setToolTip("Remove the currently selected pair from the list")
        
        edit_btn_layout.addWidget(self.btn_add_single)
        edit_btn_layout.addWidget(self.btn_edit_label)
        edit_btn_layout.addWidget(self.btn_remove_pair)
        
        gl.addLayout(edit_btn_layout, 1, 2, 1, 2, alignment=Qt.AlignRight)

        self.list_pairs = QListWidget()
        self.list_pairs.setMinimumHeight(40)
        self.list_pairs.currentRowChanged.connect(self._on_pair_selected)
        gl.addWidget(self.list_pairs, 2, 0, 1, 4)

        gl.addWidget(QLabel("Default merge tol (s):"), 3, 0)
        self.tol_default = QDoubleSpinBox()
        self.tol_default.setDecimals(3)
        self.tol_default.setSingleStep(0.005)
        self.tol_default.setRange(0.0, 10.0)
        self.tol_default.setValue(0.06)
        self.tol_default.setFont(f)
        gl.addWidget(self.tol_default, 3, 1)

        gl.addWidget(QLabel("Per-curve tol (s):"), 3, 2)
        self.tol_pair = QDoubleSpinBox()
        self.tol_pair.setDecimals(3)
        self.tol_pair.setSingleStep(0.005)
        self.tol_pair.setRange(0.0, 10.0)
        self.tol_pair.setValue(0.06)
        self.tol_pair.setEnabled(False)
        self.tol_pair.setFont(f)
        self.tol_pair.valueChanged.connect(self._update_selected_pair_tol)
        gl.addWidget(self.tol_pair, 3, 3)

        self.chk_yield = QCheckBox("Calc YS (0.2%)")
        self.chk_yield.setChecked(True)
        gl.addWidget(self.chk_yield, 4, 0, 1, 2)

        gl.addWidget(QLabel("Geometry:"), 5, 0)
        self.geom = GeometryInput()
        gl.addWidget(self.geom, 5, 1, 1, 3)

        gl.addWidget(QLabel("Manual fit range (%):"), 6, 0)
        self.start_box = QDoubleSpinBox()
        self.start_box.setDecimals(4)
        self.start_box.setRange(0.0, 100.0)
        self.start_box.setSingleStep(0.01)
        self.start_box.setValue(0.0)
        gl.addWidget(self.start_box, 6, 1)
        
        self.end_box = QDoubleSpinBox()
        self.end_box.setDecimals(4)
        self.end_box.setRange(0.0, 100.0)
        self.end_box.setSingleStep(0.01)
        self.end_box.setValue(0.0)
        gl.addWidget(self.end_box, 6, 2)
        
        self.btn_manual_fit = QPushButton("Fit by Range")
        self.btn_manual_fit.clicked.connect(self._manual_fit)
        gl.addWidget(self.btn_manual_fit, 6, 3)

        self.btn_plot = QPushButton("Generate Multi Curve")
        self.btn_plot.clicked.connect(self.plot_multi)
        
        self.btn_save_img_multi = QPushButton("Save Graph")
        self.btn_save_img_multi.clicked.connect(self.save_graph)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_plot)
        btn_layout.addWidget(self.btn_save_img_multi)
        gl.addLayout(btn_layout, 7, 0, 1, 4)

        fig = Figure(figsize=(6, 4), dpi=110)
        self.canvas = ZoomableCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)

        plot_v = QVBoxLayout()
        plot_v.setContentsMargins(0, 0, 0, 0)
        plot_v.addWidget(self.toolbar)
        plot_v.addWidget(self.canvas)
        plot_wrap = QWidget()
        plot_wrap.setLayout(plot_v)

        top = QWidget()
        top_v = QVBoxLayout(top)
        top_v.setContentsMargins(0, 0, 0, 0)
        top_v.setSpacing(8)
        top_v.addWidget(ctrl)
        
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(top)
        self.splitter.addWidget(plot_wrap)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setSizes([320, 900])

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)
        root.addWidget(self.splitter)

    def _on_mouse_press(self, event):
        """우클릭으로 Pan 시작"""
        if self.toolbar.mode != "" or event.inaxes != self.canvas.figure.axes[0]: 
            return
        if event.button == 3:
            ax = self.canvas.figure.axes[0]
            self._pan_info = {
                'active': True, 
                'start_x': event.x, 
                'start_y': event.y, 
                'start_xlim': ax.get_xlim(), 
                'start_ylim': ax.get_ylim()
            }
            if self.selector: 
                self.selector.set_active(False)

    def _on_mouse_move(self, event):
        """Pan 중 마우스 이동"""
        if self._pan_info.get('active'):
            ax = self.canvas.figure.axes[0]
            dx = event.x - self._pan_info['start_x']
            dy = event.y - self._pan_info['start_y']
            x1, x2 = self._pan_info['start_xlim']
            y1, y2 = self._pan_info['start_ylim']
            pix_x, pix_y = ax.transData.transform((x1, y1))
            pix_x -= dx
            pix_y -= dy
            new_x, new_y = ax.transData.inverted().transform((pix_x, pix_y))
            ddx = new_x - x1
            ddy = new_y - y1
            ax.set_xlim(x1 + ddx, x2 + ddx)
            ax.set_ylim(y1 + ddy, y2 + ddy)
            self.canvas.draw_idle()

    def _on_mouse_release(self, event):
        """우클릭 해제로 Pan 종료"""
        if event.button == 3:
            self._pan_info = {'active': False}
            if self.selector: 
                self.selector.set_active(True)
            self.canvas.draw_idle()

    @staticmethod
    def _stem(p):
        """파일 경로에서 확장자를 제외한 파일명 추출"""
        return os.path.splitext(os.path.basename(p))[0]
    
    @staticmethod
    def _extract_common_prefix(utm_stem, dic_stem):
        """
        UTM과 DIC 파일명에서 공통 접두사를 추출
        
        전략:
        1. 문자 단위로 앞에서부터 비교하여 일치하는 부분 추출
        2. 너무 짧으면 언더스코어/하이픈 기준으로 단어 단위 비교
        3. 그래도 없으면 숫자만 추출하여 매칭
        """
        # 1단계: 문자 단위 공통 접두사
        common = []
        for u_char, d_char in zip(utm_stem, dic_stem):
            if u_char == d_char:
                common.append(u_char)
            else:
                break
        
        common_prefix = ''.join(common).rstrip('_-. ')
        
        # 2단계: 너무 짧으면 단어 단위로 재시도
        if len(common_prefix) < 3:
            utm_parts = utm_stem.replace('-', '_').split('_')
            dic_parts = dic_stem.replace('-', '_').split('_')
            
            common_parts = []
            for u_part, d_part in zip(utm_parts, dic_parts):
                if u_part == d_part:
                    common_parts.append(u_part)
                else:
                    break
            
            if common_parts:
                common_prefix = '_'.join(common_parts)
        
        # 3단계: 여전히 짧으면 숫자만 추출
        if len(common_prefix) < 2:
            utm_digits = ''.join(ch for ch in utm_stem if ch.isdigit())
            dic_digits = ''.join(ch for ch in dic_stem if ch.isdigit())
            
            if utm_digits and utm_digits == dic_digits:
                common_prefix = f"sample{utm_digits}"
            else:
                # 최후: UTM 파일명에서 접미사 제거
                common_prefix = utm_stem
                for suffix in ['_load', '_force', '_utm', '_test', '_data']:
                    if common_prefix.lower().endswith(suffix):
                        common_prefix = common_prefix[:-len(suffix)]
                        break
        
        return common_prefix if common_prefix else utm_stem

    def _ensure_unique_label(self, base_label):
        """
        라벨이 중복되지 않도록 자동으로 증분
        예: "sample01" → "sample01_1", "sample01_2", ...
        """
        existing_labels = {p["label"] for p in self.pairs}
        
        if base_label not in existing_labels:
            return base_label
        
        counter = 1
        while f"{base_label}_{counter}" in existing_labels:
            counter += 1
        
        return f"{base_label}_{counter}"

    def _add_single_pair(self):
        """하나의 UTM + DIC 파일 쌍을 수동으로 추가"""
        utm_file, _ = QFileDialog.getOpenFileName(
            self, 
            "Select UTM CSV", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        if not utm_file:
            return
        
        dic_file, _ = QFileDialog.getOpenFileName(
            self, 
            "Select DIC CSV", 
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        if not dic_file:
            QMessageBox.information(self, "Cancelled", "DIC file selection cancelled.")
            return
        
        # ========== 추가: 동일 파일 선택 방지 ==========
        if utm_file == dic_file:
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "UTM and DIC files must be different!\n"
                f"You selected the same file:\n{os.path.basename(utm_file)}"
            )
            return
        
        # 공통 접두사 추출
        utm_stem = self._stem(utm_file)
        dic_stem = self._stem(dic_file)
        
        # ========== 추가: 파일명(stem)이 동일한 경우도 경고 ==========
        if utm_stem == dic_stem:
            reply = QMessageBox.question(
                self,
                "Same Filename Warning",
                f"UTM and DIC have identical filenames (excluding extension):\n"
                f"  '{utm_stem}'\n\n"
                f"This usually means you selected the wrong files.\n"
                f"Continue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        default_label = self._extract_common_prefix(utm_stem, dic_stem)
        default_label = self._ensure_unique_label(default_label)
        
        label, ok = QInputDialog.getText(
            self, 
            "Enter Pair Label", 
            "Label for this pair (auto-detected):", 
            text=default_label
        )
        
        if not ok or not label.strip():
            label = default_label
        else:
            label = label.strip()
            existing_labels = {p["label"] for p in self.pairs}
            if label in existing_labels:
                QMessageBox.warning(
                    self,
                    "Duplicate Label",
                    f"Label '{label}' already exists.\nAuto-incrementing to unique name."
                )
                label = self._ensure_unique_label(label)
        
        new_pair = {
            "utm": utm_file, 
            "dic": dic_file, 
            "label": label, 
            "tol": self.tol_default.value()
        }
        self.pairs.append(new_pair)
        
        if utm_file not in self.utm_files:
            self.utm_files.append(utm_file)
        if dic_file not in self.dic_files:
            self.dic_files.append(dic_file)
        
        self._refresh_pair_list()
        self.list_pairs.setCurrentRow(len(self.pairs) - 1)
        
        QMessageBox.information(
            self, 
            "Pair Added", 
            f"Added pair:\n  Label: {label}\n"
            f"  UTM: {os.path.basename(utm_file)}\n"
            f"  DIC: {os.path.basename(dic_file)}"
        )

    def _edit_selected_label(self):
        """선택된 Pair의 라벨을 수정"""
        row = self.list_pairs.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, 
                "No Selection", 
                "Please select a pair from the list to edit."
            )
            return
        
        if 0 <= row < len(self.pairs):
            current_label = self.pairs[row]["label"]
            new_label, ok = QInputDialog.getText(
                self, 
                "Edit Pair Label", 
                "Enter new label:", 
                text=current_label
            )
            
            if ok and new_label.strip():
                # 중복 확인 (자기 자신 제외)
                existing_labels = {
                    p["label"] for i, p in enumerate(self.pairs) if i != row
                }
                
                final_label = new_label.strip()
                if final_label in existing_labels:
                    QMessageBox.warning(
                        self,
                        "Duplicate Label",
                        f"Label '{final_label}' already exists. Please choose a different name."
                    )
                    return
                
                self.pairs[row]["label"] = final_label
                self._refresh_pair_list()
                self.list_pairs.setCurrentRow(row)

    def _remove_selected_pair(self):
        """선택된 Pair 삭제"""
        row = self.list_pairs.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, 
                "No Selection", 
                "Please select a pair from the list to remove."
            )
            return

        if 0 <= row < len(self.pairs):
            removed_pair = self.pairs[row]
            del self.pairs[row]
            self._refresh_pair_list()
            
            new_count = len(self.pairs)
            if new_count > 0:
                new_row = min(row, new_count - 1)
                self.list_pairs.setCurrentRow(new_row)
            
            QMessageBox.information(
                self, 
                "Pair Removed", 
                f"Removed: {removed_pair['label']}"
            )

    def load_multiple_sets(self):
        """여러 UTM+DIC 파일을 한 번에 로드"""
        utm_files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select multiple UTM CSVs", 
            "", 
            "CSV (*.csv)"
        )
        if not utm_files: 
            return
        
        dic_files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select multiple DIC CSVs", 
            "", 
            "CSV (*.csv)"
        )
        if not dic_files:
            QMessageBox.information(self, "Info", "DIC selection cancelled.")
            return
        
        self.utm_files = sorted(utm_files)
        self.dic_files = sorted(dic_files)
        
        base_pairs = self._guess_pairs(self.utm_files, self.dic_files)
        
        # ========== 추가: 동일 파일 쌍 필터링 ==========
        valid_pairs = []
        invalid_count = 0
        
        for (u, d, label) in base_pairs:
            # 완전히 동일한 파일
            if u == d:
                invalid_count += 1
                print(f"[WARN] Skipped same file: {os.path.basename(u)}")
                continue
            
            # 파일명(stem)이 동일한 경우
            if self._stem(u) == self._stem(d):
                invalid_count += 1
                print(f"[WARN] Skipped same filename: {self._stem(u)}")
                continue
            
            valid_pairs.append((u, d, label))
        
        # 경고 메시지
        if invalid_count > 0:
            QMessageBox.warning(
                self,
                "Invalid Pairs Detected",
                f"Skipped {invalid_count} pair(s) where UTM and DIC files were identical.\n"
                f"Please check your file selection."
            )
        
        if not valid_pairs:
            QMessageBox.warning(
                self,
                "No Valid Pairs",
                "No valid UTM-DIC pairs found after filtering.\n"
                "Make sure UTM and DIC files have different names."
            )
            return
        
        # 중복 라벨 방지하면서 추가
        self.pairs = []
        for (u, d, label) in valid_pairs:
            unique_label = self._ensure_unique_label(label)
            self.pairs.append({
                "utm": u, 
                "dic": d, 
                "label": unique_label, 
                "tol": self.tol_default.value()
            })
        
        self._refresh_pair_list()
        if self.pairs:
            self.list_pairs.setCurrentRow(0)
        
        QMessageBox.information(
            self,
            "Load Complete",
            f"Successfully loaded {len(self.pairs)} valid pair(s)."
        )

    def _refresh_pair_list(self):
        """Pair 리스트 UI 갱신"""
        self.list_pairs.clear()
        for i, p in enumerate(self.pairs, 1):
            self.list_pairs.addItem(
                f"{i:02d}. {p['label']} | tol={p['tol']:.3f}s | "
                f"UTM={os.path.basename(p['utm'])} / DIC={os.path.basename(p['dic'])}"
            )
        self.lbl_summary.setText(
            f"UTM: {len(self.utm_files)}, DIC: {len(self.dic_files)}, Pairs: {len(self.pairs)}"
        )
        self.tol_pair.setEnabled(False)

    def _on_pair_selected(self, row):
        """리스트에서 Pair 선택 시"""
        if 0 <= row < len(self.pairs):
            self.tol_pair.blockSignals(True)
            self.tol_pair.setEnabled(True)
            self.tol_pair.setValue(float(self.pairs[row]["tol"]))
            self.tol_pair.blockSignals(False)
        else:
            self.tol_pair.setEnabled(False)

    def _update_selected_pair_tol(self, val):
        """선택된 Pair의 tolerance 값 업데이트"""
        row = self.list_pairs.currentRow()
        if 0 <= row < len(self.pairs):
            self.pairs[row]["tol"] = float(val)
            self.list_pairs.item(row).setText(
                f"{row+1:02d}. {self.pairs[row]['label']} | tol={val:.3f}s | "
                f"UTM={os.path.basename(self.pairs[row]['utm'])} / "
                f"DIC={os.path.basename(self.pairs[row]['dic'])}"
            )

    def _guess_pairs(self, utm_list, dic_list):
        """
        UTM과 DIC 파일 목록으로부터 자동으로 쌍을 추정
        
        전략:
        1. 파일명에서 공통 접두사 추출
        2. 동일한 숫자가 있으면 매칭
        3. stem이 완전히 일치하면 매칭
        """
        pairs = []
        if not utm_list or not dic_list: 
            return pairs
        
        # 1단계: 숫자 기반 매칭
        def extract_digits(s):
            return ''.join(ch for ch in s if ch.isdigit()) or None
        
        utm_digit_map = {}
        for u in utm_list:
            digits = extract_digits(self._stem(u))
            if digits:
                utm_digit_map[digits] = u
        
        dic_digit_map = {}
        for d in dic_list:
            digits = extract_digits(self._stem(d))
            if digits:
                dic_digit_map[digits] = d
        
        digit_keys = [k for k in utm_digit_map if k in dic_digit_map]
        digit_keys = sorted(digit_keys, key=lambda x: int(x))
        
        for k in digit_keys:
            utm_stem = self._stem(utm_digit_map[k])
            dic_stem = self._stem(dic_digit_map[k])
            label = self._extract_common_prefix(utm_stem, dic_stem)
            pairs.append((utm_digit_map[k], dic_digit_map[k], label))
        
        # 2단계: stem 완전 일치 매칭
        paired_utm = {u for u, _, _ in pairs}
        paired_dic = {d for _, d, _ in pairs}
        
        rem_utm = [u for u in utm_list if u not in paired_utm]
        rem_dic = [d for d in dic_list if d not in paired_dic]
        
        stems_dic = {self._stem(d): d for d in rem_dic}
        for u in rem_utm[:]:
            s = self._stem(u)
            if s in stems_dic:
                d = stems_dic[s]
                label = self._extract_common_prefix(s, self._stem(d))
                pairs.append((u, d, label))
                rem_utm.remove(u)
        
        # 3단계: 남은 파일은 순서대로 매칭
        for u, d in zip(sorted(rem_utm), sorted(rem_dic)):
            utm_stem = self._stem(u)
            dic_stem = self._stem(d)
            label = self._extract_common_prefix(utm_stem, dic_stem)
            pairs.append((u, d, label))
        
        return sorted(pairs, key=lambda x: x[2])

    def _clear_span(self):
        """범위 선택 표시 제거"""
        if getattr(self, "span", None) is not None:
            try: 
                self.span.remove()
            except Exception: 
                pass
            self.span = None
        for ln in getattr(self, "vlines", []):
            try: 
                ln.remove()
            except Exception: 
                pass
        self.vlines = []

    def _init_span_selector(self, ax):
        """SpanSelector 초기화 (탄성계수 측정용)"""
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
            props=dict(facecolor="#00BCD4", alpha=0.22, edgecolor="#00ACC1"),
            interactive=True, 
            drag_from_anywhere=True,
            button=1 
        )
        for attr in ("ignore_event_outside", "ignore_events_outside"):
            if hasattr(self.selector, attr): 
                setattr(self.selector, attr, False)

    @staticmethod
    def _fit_slope(xs, ys):
        """선형 피팅으로 기울기(탄성계수) 계산"""
        n = len(xs)
        if n >= 3:
            a, _ = np.polyfit(xs, ys, 1)
            return float(a)
        elif n == 2:
            if xs[1] == xs[0]: 
                return np.nan
            return float((ys[1] - ys[0]) / (xs[1] - xs[0]))
        return np.nan

    def _ensure_side_panel(self, fig):
        """사이드 패널 (속성 표시 영역) 생성"""
        fig.subplots_adjust(top=1.0, bottom=0.2, right=0.65)
        
        if self.ax_info is None or self.ax_info not in fig.axes:
            self.ax_info = fig.add_axes([0.67, 0.12, 0.32, 0.76])
        ax = self.ax_info
        ax.clear()
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)
        ax.set_facecolor("none")
        ax.set_title(
            "E (Modulus) & UTS", 
            color="black", 
            fontsize=12, 
            fontweight="bold", 
            pad=4
        )

    def plot_multi(self):
        """여러 곡선을 한 번에 플롯"""
        if not self.pairs:
            QMessageBox.information(self, "Info", "Load UTM/DIC files first.")
            return

        self.datasets = []
        self._clear_span()
        
        try:
            w_mm, t_mm, _ = self.geom.get()
            if w_mm * t_mm == 0:
                 QMessageBox.warning(self, "Error", "Geometry(면적)는 0이 될 수 없습니다.")
                 return
            A = (w_mm * 1e-3) * (t_mm * 1e-3)
        except ValueError:
            return

        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        calc_yield = self.chk_yield.isChecked()

        for idx, p in enumerate(self.pairs):
            utm_path, dic_path, tol = p["utm"], p["dic"], float(p["tol"])
            label = p["label"]
            try:
                udf = safe_read_csv(utm_path)
                udf.columns = [c.strip() for c in udf.columns]
                
                ddf = safe_read_csv(dic_path)
                ddf.columns = [c.strip() for c in ddf.columns]
                
                td_col_name = ddf.columns[0]
                if pd.api.types.is_numeric_dtype(ddf[td_col_name]):
                    ddf[td_col_name] = ddf[td_col_name] - ddf[td_col_name].iloc[0]

                tu_col_name = udf.columns[0]
                if pd.api.types.is_numeric_dtype(udf[tu_col_name]):
                    udf[tu_col_name] = udf[tu_col_name] - udf[tu_col_name].iloc[0]

                tu = udf.columns[0]
                nums_u = udf.select_dtypes(include='number').columns.tolist()
                load_cols = [
                    c for c in nums_u if c != tu and 
                    ("load" in c.lower() or "force" in c.lower())
                ] or [c for c in nums_u if c != tu]
                
                if not load_cols: 
                    continue
                lc = load_cols[0]
                
                td = ddf.columns[0]
                nums_d = ddf.select_dtypes(include='number').columns.tolist()
                dic_cols = [
                    c for c in nums_d if c != td and 
                    any(k in c.lower() for k in ["strain", "ε", "exx", "eyy", "e_"])
                ] or [c for c in nums_d if c != td]
                
                if not dic_cols: 
                    continue
                sx = dic_cols[0]

                udf = udf.sort_values(tu)
                ddf = ddf.sort_values(td)
                
                m = pd.merge_asof(
                    udf[[tu, lc]], 
                    ddf[[td, sx]], 
                    left_on=tu, 
                    right_on=td,
                    direction="nearest", 
                    tolerance=tol
                ).dropna(subset=[sx])
                
                if m.empty:
                    print(f"[WARN] Merge result is empty for {label}. "
                          "Check time columns or tolerance.")
                    continue

                eps_eng = m[sx].astype(float) / 100.0
                eps_true = np.log1p(eps_eng)
                sig_eng = (m[lc] - m[lc].iloc[0]) / A / 1e6
                sig_true = sig_eng * (1.0 + eps_eng)

                eps_use = (eps_true - eps_true.iloc[0]).values
                sig_use = (sig_true - sig_true.iloc[0]).values

                color = self.SK_COLORS[idx % len(self.SK_COLORS)]
                ax.plot(eps_use * 100.0, sig_use, '-', color=color, label=label)

                uts = float(np.nanmax(sig_use))
                
                ys_val = None
                if calc_yield:
                    ys, ys_idx, _ = calculate_yield_strength(eps_use, sig_use)
                    if ys is not None:
                        ys_val = ys
                        ax.plot(
                            eps_use[ys_idx] * 100.0, 
                            ys, 
                            'o', 
                            color=color, 
                            markersize=6, 
                            markeredgecolor='white'
                        )

                self.datasets.append({
                    "label": label, 
                    "color": color, 
                    "eps": eps_use, 
                    "sig": sig_use, 
                    "uts": uts, 
                    "ys": ys_val
                })
            except Exception as e:
                print(f"[WARN] {os.path.basename(utm_path)} / "
                      f"{os.path.basename(dic_path)} : {e}")

        ax.set_xlabel("True Strain (%)")
        ax.set_ylabel("True Stress (MPa)")
        ax.legend(loc="upper left", frameon=True)
        
        self._ensure_side_panel(fig)
        self._render_info_panel(
            rows=[(d["label"], d["color"], None, d["uts"], d.get("ys")) 
                  for d in self.datasets]
        )

        self.canvas.draw()
        if self.datasets: 
            self._init_span_selector(ax)

    def _render_info_panel(self, rows):
        """사이드 패널에 속성 정보 표시"""
        self._ensure_side_panel(self.canvas.figure)
        ax = self.ax_info

        ax.clear()
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)
        ax.set_facecolor("none")
        
        try:
            show_ys = self.chk_yield.isChecked()
        except AttributeError:
            show_ys = True

        title_str = "Properties (E, UTS, YS)" if show_ys else "Properties (E, UTS)"
        ax.set_title(title_str, color="black", fontsize=13, fontweight="bold", pad=4)

        y = 0.92
        for row_data in rows:
            label, color, E_mpa, uts = row_data[:4]
            ys_val = row_data[4] if len(row_data) > 4 else None

            e_txt = "E=–" if (E_mpa is None or not np.isfinite(E_mpa)) \
                    else f"E={E_mpa/1000.0:.3f} GPa"
            u_txt = f"UTS={uts:.1f}"
            
            if show_ys:
                y_txt = f"YS={ys_val:.1f}" if ys_val is not None else "YS=–"
                info_str = f"{e_txt} | {u_txt} | {y_txt} MPa"
            else:
                info_str = f"{e_txt} | {u_txt} MPa"

            ax.text(
                0.0, y, f"{label}", 
                transform=ax.transAxes, 
                ha="left", va="center", 
                fontsize=11, color=color, fontweight="bold"
            )
            ax.text(
                0.0, y - 0.055, info_str, 
                transform=ax.transAxes, 
                ha="left", va="center", 
                fontsize=10.5, color="#333"
            )
            y -= 0.13

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        self.canvas.draw_idle()

    def _on_select(self, x_min, x_max):
        """SpanSelector로 범위 선택 완료 시 탄성계수 계산"""
        if not self.datasets or x_max <= x_min: 
            return
        if (x_max - x_min) < 0.0001:
            pad = 0.00005
            x_min -= pad
            x_max += pad

        eps_min = x_min / 100.0
        eps_max = x_max / 100.0

        self._clear_span()
        ax = self.canvas.figure.axes[0]
        self.span = ax.axvspan(x_min, x_max, color="#00BCD4", alpha=0.22, zorder=0.5)
        self.vlines = [
            ax.axvline(x_min, color="#00ACC1", lw=2, zorder=1.5),
            ax.axvline(x_max, color="#00ACC1", lw=2, zorder=1.5),
        ]

        rows = []
        for d in self.datasets:
            eps = d["eps"]
            sig = d["sig"]
            msk = (eps >= eps_min) & (eps <= eps_max)
            xs = eps[msk]
            ys = sig[msk]
            E_mpa = self._fit_slope(xs, ys)
            rows.append((d["label"], d["color"], E_mpa, d["uts"], d.get("ys")))

        self._render_info_panel(rows=rows)

    def _manual_fit(self):
        """수동으로 입력한 범위에서 탄성계수 계산"""
        if not self.datasets:
            QMessageBox.information(self, "Info", "Generate curves first.")
            return
        
        x_min = float(self.start_box.value())
        x_max = float(self.end_box.value())
        
        if x_max <= x_min:
            QMessageBox.warning(self, "Error", "End (%) must be greater than Start (%).")
            return

        self._clear_span()
        ax = self.canvas.figure.axes[0]
        self.span = ax.axvspan(x_min, x_max, color="#00BCD4", alpha=0.22, zorder=0.5)
        self.vlines = [
            ax.axvline(x_min, color="#00ACC1", lw=2, zorder=1.5),
            ax.axvline(x_max, color="#00ACC1", lw=2, zorder=1.5),
        ]

        eps_min = x_min / 100.0
        eps_max = x_max / 100.0
        
        rows = []
        for d in self.datasets:
            eps = d["eps"]
            sig = d["sig"]
            msk = (eps >= eps_min) & (eps <= eps_max)
            xs = eps[msk]
            ys = sig[msk]
            E_mpa = self._fit_slope(xs, ys) if len(xs) >= 2 else np.nan
            rows.append((d["label"], d["color"], E_mpa, d["uts"], d.get("ys")))
        
        self._render_info_panel(rows=rows)
        self.canvas.draw_idle()

    def save_graph(self):
        """그래프를 이미지로 저장"""
        if self.canvas.figure is None:
            QMessageBox.warning(self, "Error", "No graph to save.")
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Multi-Compare Graph", 
            "multi_compare.png", 
            "PNG Image (*.png);;JPEG Image (*.jpg);;PDF Document (*.pdf)"
        )
        if not path:
            return
            
        try:
            self.canvas.figure.savefig(path, dpi=300, bbox_inches='tight')
            QMessageBox.information(
                self, 
                "Saved", 
                f"Graph saved to:\n{os.path.basename(path)}"
            )
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Failed to save graph:\n{e}")


# ── Main Application
class MainWindow(QWidget):
    """메인 윈도우 (3개 탭 통합)"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SS Curve Generator / Preprocessor / Multi Compare")
        self.resize(1600, 980)

        tabs = QTabWidget()
        tabs.addTab(TabDICUTM(), "SS Curve Generator")
        tabs.addTab(TabPreprocessor(), "CSV Preprocessor")
        tabs.addTab(TabMultiCompare(), "Multi Compare")
        
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)
        root.addWidget(tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 개선 2: 폰트 존재 여부 확인 후 설정
    available_families = QFontDatabase().families()
    if "Pretendard" in available_families:
        app_font = QFont("Pretendard", 13, QFont.DemiBold)
    else:
        app_font = QFont("Arial", 13, QFont.Bold)
    app.setFont(app_font)

    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
