# Data_Repack.py

import sys, os
import numpy as np
import pandas as pd
import matplotlib as mpl

import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFileDialog, QLabel, QComboBox, QPushButton, QGroupBox, QLineEdit,
    QMessageBox, QDoubleSpinBox, QCheckBox, QSplitter, QSizePolicy, QListWidget,
    QInputDialog
)

from PyQt5.QtGui import QFont
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

def font_big():
    try:
        font = QFont("Pretendard", 13, QFont.DemiBold)
    except Exception:
        font = QFont("Arial", 13, QFont.Bold)
    return font

def font_small():
    try:
        f = QFont("Pretendard", 9)
    except Exception:
        f = QFont("Arial", 9)
    f.setWeight(QFont.Normal)
    return f

def safe_read_csv(path, **kw):
    try:
        return pd.read_csv(path, **kw)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="cp949", **kw)

#  항복 강도 계산 (0.2% Offset Method)
def calculate_yield_strength(strain, stress, offset_percent=0.2):
    """
    0.2% 오프셋 방법을 사용하여 항복강도를 계산
    strain: 절대값 (예: 0.01 = 1%)
    stress: MPa
    """
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
    def __init__(self, fig):
        super().__init__(fig)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.mpl_connect('scroll_event', self.on_scroll)

    def on_scroll(self, event):
        if event.inaxes is None: return
        ax = event.inaxes
        base_scale = 1.1
        if event.button == 'up': scale_factor = 1 / base_scale
        elif event.button == 'down': scale_factor = base_scale
        else: return

        cur_xlim = ax.get_xlim(); cur_ylim = ax.get_ylim()
        xdata = event.xdata; ydata = event.ydata
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


PRESET_FILE = "specimen_presets.json"


# ── Geometry
class GeometryInput(QWidget):
    def __init__(self, w="3.8", t="0.08", L0="50"):
        super().__init__()
        f = font_big()
        self.presets = {}

        self.w = QLineEdit(w);  self.w.setFont(f); self.w.setFixedWidth(80)
        self.t = QLineEdit(t);  self.t.setFont(f); self.t.setFixedWidth(80)
        self.L0= QLineEdit(L0); self.L0.setFont(f); self.L0.setFixedWidth(80)
        
        row = QHBoxLayout(); row.setContentsMargins(0,0,0,0); row.setSpacing(10)
        row.addWidget(QLabel("Width [mm]"));   row.addWidget(self.w)
        row.addWidget(QLabel("Thickness [mm]")); row.addWidget(self.t)
        row.addWidget(QLabel("Gauge [mm]")); row.addWidget(self.L0)
        row.addStretch(1)

        preset_row = QHBoxLayout()
        preset_row.setContentsMargins(0, 5, 0, 0)
        
        self.cmb_presets = QComboBox()
        self.cmb_presets.setFont(f)
        self.cmb_presets.setPlaceholderText("--- Select Preset ---")
        
        self.btn_save_preset = QPushButton("Save"); self.btn_save_preset.setFont(f)
        self.btn_del_preset = QPushButton("Del"); self.btn_del_preset.setFont(f)
        
        preset_row.addWidget(QLabel("Preset:"))
        preset_row.addWidget(self.cmb_presets, 1)
        preset_row.addWidget(self.btn_save_preset)
        preset_row.addWidget(self.btn_del_preset)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(5)
        main_layout.addLayout(row)
        main_layout.addLayout(preset_row)

        self._load_presets()
        self.cmb_presets.activated.connect(self._apply_preset)
        self.btn_save_preset.clicked.connect(self._save_preset)
        self.btn_del_preset.clicked.connect(self._delete_preset)

    def get(self): 
        try:
            w_val = float(self.w.text())
            t_val = float(self.t.text())
            L0_val = float(self.L0.text())
            return w_val, t_val, L0_val
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", f"숫자 변환 실패: {e}\n유효한 숫자를 입력하세요.")
            raise ValueError(f"입력값 오류: {e}")

    def _load_presets(self):
        self.cmb_presets.blockSignals(True)
        self.cmb_presets.clear()
        
        if os.path.exists(PRESET_FILE):
            try:
                with open(PRESET_FILE, 'r', encoding='utf-8') as f:
                    self.presets = json.load(f)
            except Exception as e:
                self.presets = {}
        else:
            self.presets = {}
        
        if self.presets:
            self.cmb_presets.addItems(sorted(self.presets.keys()))
        
        self.cmb_presets.setCurrentIndex(-1)
        self.cmb_presets.blockSignals(False)

    def _apply_preset(self, index):
        name = self.cmb_presets.itemText(index)
        if name in self.presets:
            data = self.presets[name]
            self.w.setText(data.get("w", "0"))
            self.t.setText(data.get("t", "0"))
            self.L0.setText(data.get("L0", "0"))
            
    def _save_preset(self):
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
        name = self.cmb_presets.currentText()
        if not name or name not in self.presets:
            QMessageBox.warning(self, "Error", "삭제할 프리셋이 선택되지 않았습니다.")
            return

        reply = QMessageBox.question(self, "Delete Preset",
                                     f"정말 '{name}' 프리셋을 삭제하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if name in self.presets:
                del self.presets[name]
                self._save_to_file()
                self._load_presets()

    def _save_to_file(self):
        try:
            with open(PRESET_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, indent=4, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"프리셋 저장 실패: {e}")


# ── Tab 1: SS Curve Generator
class TabDICUTM(QWidget):
    def __init__(self):
        super().__init__()
        f = font_big()
        self.udf = None; self.ddf = None; self.out_df = None
        
        self._pan_info = {} # Pan 초기화

        ctrl = QGroupBox("Load · Settings"); ctrl.setFont(f)
        gl = QGridLayout(ctrl); gl.setHorizontalSpacing(10); gl.setVerticalSpacing(8)

        self.btn_utm = QPushButton("Load UTM CSV"); self.btn_dic = QPushButton("Load DIC CSV")
        for b in (self.btn_utm, self.btn_dic): b.setFont(f)
        self.btn_utm.clicked.connect(self.load_utm); self.btn_dic.clicked.connect(self.load_dic)
        self.lbl_utm = QLabel("UTM: -"); self.lbl_dic = QLabel("DIC: -")
        gl.addWidget(self.btn_utm, 0,0); gl.addWidget(self.lbl_utm, 0,1,1,3)
        gl.addWidget(self.btn_dic, 1,0); gl.addWidget(self.lbl_dic, 1,1,1,3)

        gl.addWidget(QLabel("UTM Load (N):"), 2,0)
        self.cmb_load = QComboBox(); self.cmb_load.setEnabled(False); self.cmb_load.setFont(f)
        gl.addWidget(self.cmb_load, 2,1)
        gl.addWidget(QLabel("DIC Strain (%):"), 2,2)
        self.cmb_dic = QComboBox(); self.cmb_dic.setEnabled(False); self.cmb_dic.setFont(f)
        gl.addWidget(self.cmb_dic, 2,3)

        gl.addWidget(QLabel("Merge tol (s):"), 3,0)
        self.tol = QDoubleSpinBox(); self.tol.setDecimals(3); self.tol.setSingleStep(0.005)
        self.tol.setRange(0.0, 10.0); self.tol.setValue(0.06); self.tol.setFont(f); gl.addWidget(self.tol, 3,1)
        
        # [New] 항복점 계산 여부 체크박스 (기본값 True)
        self.chk_yield = QCheckBox("Calc Yield Strength (0.2%)")
        self.chk_yield.setChecked(True)
        gl.addWidget(self.chk_yield, 3, 2, 1, 2)
        
        gl.addWidget(QLabel("Geometry:"), 4,0)
        self.geom = GeometryInput(); gl.addWidget(self.geom, 4,1,1,3)

        self.btn_plot = QPushButton("Generate S–S Curve"); self.btn_plot.setFont(f); self.btn_plot.clicked.connect(self.plot_ss)
        self.btn_save = QPushButton("Save CSV"); self.btn_save.setFont(f); self.btn_save.setEnabled(False); self.btn_save.clicked.connect(self.save_csv)
        
        self.btn_save_img = QPushButton("Save Graph"); self.btn_save_img.setFont(f); self.btn_save_img.setEnabled(False)
        self.btn_save_img.clicked.connect(self.save_graph)

        row = QHBoxLayout(); row.addStretch(1)
        row.addWidget(self.btn_plot)
        row.addWidget(self.btn_save)
        row.addWidget(self.btn_save_img)
        gl.addLayout(row, 5,0,1,4)

        res = QGroupBox("Results"); res.setFont(f)
        h = QHBoxLayout(res); self.lbl_uts = QLabel("UTS: - (MPa) | YS: - (MPa)"); h.addWidget(self.lbl_uts); h.addStretch(1)

        fig = Figure(figsize=(6,4), dpi=110)
        self.canvas = ZoomableCanvas(fig); self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)

        plot_v = QVBoxLayout(); plot_v.setContentsMargins(0,0,0,0); plot_v.addWidget(self.toolbar); plot_v.addWidget(self.canvas)
        plot_wrap = QWidget(); plot_wrap.setLayout(plot_v)

        top = QWidget(); top_v = QVBoxLayout(top); top_v.setContentsMargins(0,0,0,0); top_v.setSpacing(8)
        top_v.addWidget(ctrl); top_v.addWidget(res)

        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(top); self.splitter.addWidget(plot_wrap)
        self.splitter.setChildrenCollapsible(False); self.splitter.setSizes([320, 900])

        root = QVBoxLayout(self); root.setContentsMargins(8,8,8,8); root.setSpacing(8); root.addWidget(self.splitter)
        ctrl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum); res.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum); top.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

    # [Pan] 3. 이벤트 핸들러
    def _on_mouse_press(self, event):
        if self.toolbar.mode != "" or event.inaxes != self.canvas.figure.axes[0]: return
        if event.button == 3: # Right click
            ax = self.canvas.figure.axes[0]
            self._pan_info = {'active': True, 'start_x': event.x, 'start_y': event.y, 'start_xlim': ax.get_xlim(), 'start_ylim': ax.get_ylim()}

    def _on_mouse_move(self, event):
        if self._pan_info.get('active'):
            ax = self.canvas.figure.axes[0]
            dx = event.x - self._pan_info['start_x']
            dy = event.y - self._pan_info['start_y']
            x1, x2 = self._pan_info['start_xlim']; y1, y2 = self._pan_info['start_ylim']
            pix_x, pix_y = ax.transData.transform((x1, y1))
            pix_x -= dx; pix_y -= dy
            new_x, new_y = ax.transData.inverted().transform((pix_x, pix_y))
            ddx = new_x - x1; ddy = new_y - y1
            ax.set_xlim(x1+ddx, x2+ddx); ax.set_ylim(y1+ddy, y2+ddy)
            self.canvas.draw_idle()

    def _on_mouse_release(self, event):
        if event.button == 3: self._pan_info = {'active': False}

    def load_utm(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select UTM CSV", "", "CSV (*.csv);;All Files (*)")
        if not path: return
        try:
            df = safe_read_csv(path); df.columns = [c.strip() for c in df.columns]
            self.udf = df; self.lbl_utm.setText(f"UTM: {os.path.basename(path)}")
            nums = df.select_dtypes(include='number').columns.tolist()
            if nums:
                t0 = df.columns[0]
                others = [c for c in nums if c != t0]
                pref = [c for c in others if ("load" in c.lower() or "force" in c.lower())] or others
                self.cmb_load.clear(); self.cmb_load.addItems(pref); self.cmb_load.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "UTM Load Error", str(e))

    def load_dic(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select DIC CSV", "", "CSV (*.csv);;All Files (*)")
        if not path: return
        try:
            df = safe_read_csv(path); df.columns = [c.strip() for c in df.columns]
            
            time_col = df.columns[0]
            if pd.api.types.is_numeric_dtype(df[time_col]):
                df[time_col] = df[time_col] - df[time_col].iloc[0]


            self.ddf = df; self.lbl_dic.setText(f"DIC: {os.path.basename(path)}")
            nums = df.select_dtypes(include='number').columns.tolist()
            if nums:
                t0 = df.columns[0]
                cand = [c for c in nums if c != t0]
                pri = [c for c in cand if any(k in c.lower() for k in ["strain","ε","exx","eyy","e_"])]
                self.cmb_dic.clear(); self.cmb_dic.addItems(pri or cand); self.cmb_dic.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "DIC Load Error", str(e))

    def plot_ss(self):
        try:
            self.out_df = None; self.btn_save.setEnabled(False); self.btn_save_img.setEnabled(False)
            if self.udf is None or self.ddf is None:
                QMessageBox.warning(self, "Error", "Load both UTM and DIC files."); return
            if not (self.cmb_load.isEnabled() and self.cmb_dic.isEnabled()):
                QMessageBox.warning(self, "Error", "Select UTM load and DIC strain columns."); return

            try:
                w_mm, t_mm, _ = self.geom.get()
                if w_mm * t_mm == 0:
                    QMessageBox.warning(self, "Error", "Geometry(면적)는 0이 될 수 없습니다."); return
                A = (w_mm*1e-3) * (t_mm*1e-3)
            except ValueError:
                return

            lc = self.cmb_load.currentText(); sx = self.cmb_dic.currentText()
            tu, td = self.udf.columns[0], self.ddf.columns[0]

            udf = self.udf.sort_values(tu); ddf = self.ddf.sort_values(td)
            
            m = pd.merge_asof(udf[[tu, lc]], ddf[[td, sx]], left_on=tu, right_on=td,
                              direction="nearest", tolerance=self.tol.value()).dropna(subset=[sx])

            if m.empty:
                QMessageBox.warning(self, "Error", "Merge result is empty. Check time/tolerance."); return

            eps_eng  = m[sx].astype(float) / 100.0
            eps_true = np.log1p(eps_eng)
            sig_eng  = (m[lc] - m[lc].iloc[0]) / A / 1e6
            sig_true = sig_eng * (1.0 + eps_eng)

            eps_plot = (eps_true - eps_true.iloc[0]).values
            sig_plot = (sig_true - sig_true.iloc[0]).values

            fig = self.canvas.figure; fig.clear()
            
            # [유지] Margin 설정
            fig.subplots_adjust(top=1.0, bottom=0.2)
            
            ax = fig.add_subplot(111)
            ax.plot(eps_plot*100.0, sig_plot, '-', color=SK_RED, label="True σ–ε")
            
            uts = float(np.nanmax(sig_plot))
            
            # [Modified] 체크박스가 켜져 있을 때만 항복점 계산
            ys_text = ""
            if self.chk_yield.isChecked():
                ys, ys_idx, E_val = calculate_yield_strength(eps_plot, sig_plot)
                
                if ys is not None:
                    ys_text = f" | YS: {ys:.1f} MPa"
                    ax.plot(eps_plot[ys_idx]*100.0, ys, 'o', color='blue', label=f"YS: {ys:.1f} MPa")
                    
                    # 오프셋 라인 시각화
                    x_vis = np.linspace(0, eps_plot[ys_idx]*1.2, 50)
                    y_vis = E_val * (x_vis - 0.002) 
                    ax.plot(x_vis*100.0, y_vis, '--', color='gray', alpha=0.5, label="0.2% Offset")
                else:
                    ys_text = " | YS: Not Found"
            
            self.lbl_uts.setText(f"UTS: {uts:.1f} MPa{ys_text}")

            ax.set_xlabel("True Strain (%)"); ax.set_ylabel("True Stress (MPa)")
            ax.legend(loc="upper left", frameon=True)
            self.canvas.draw()

            self.out_df = pd.DataFrame({
                "time_utm_s": m[tu].values, "time_dic_s": m[td].values,
                "load_N": m[lc].values, "dic_percent": m[sx].values,
                "eng_eps": eps_eng.values, "true_eps": eps_true.values,
                "eng_sig_mpa": sig_eng.values, "true_sig_mpa": sig_true.values,
                "true_eps_plot": eps_plot, "true_sig_plot_mpa": sig_plot,
            })
            self.btn_save.setEnabled(True)
            self.btn_save_img.setEnabled(True)

        except Exception as e:
            QMessageBox.warning(self, "Plot Error", str(e))

    def save_csv(self):
        if self.out_df is None or self.out_df.empty:
            QMessageBox.information(self, "Info", "No data to save."); return
        path, _ = QFileDialog.getSaveFileName(self, "Save merged SS CSV", "merged_ss.csv", "CSV (*.csv)")
        if not path: return
        try:
            self.out_df.to_csv(path, index=False, encoding="utf-8-sig")
            QMessageBox.information(self, "Saved", f"Saved:\n{os.path.basename(path)}")
        except Exception as e:
            QMessageBox.warning(self, "Save Error", str(e))

    def save_graph(self):
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
            QMessageBox.information(self, "Saved", f"Graph saved to:\n{os.path.basename(path)}")
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Failed to save graph:\n{e}")


# ── Tab 2: Preprocessor
class TabPreprocessor(QWidget):
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

        # --- 1. 컨트롤 박스 ---
        ctrl = QGroupBox("CSV Preprocessor"); ctrl.setFont(f)
        gl = QGridLayout(ctrl)

        # 1a. 파일 로드
        self.btn = QPushButton("Load CSV"); self.btn.setFont(f); self.btn.clicked.connect(self.load_csv)
        self.lbl = QLabel("File: -")
        gl.addWidget(self.btn, 0, 0); gl.addWidget(self.lbl, 0, 1, 1, 3)

        # 1b. 컬럼 선택
        self.x_col_label = QLabel("X column:") 
        gl.addWidget(self.x_col_label, 1, 0)
        self.cmb_eps = QComboBox(); self.cmb_eps.setFont(f); gl.addWidget(self.cmb_eps, 1, 1)
        
        self.y_col_label = QLabel("Y column:")
        gl.addWidget(self.y_col_label, 1, 2)
        self.cmb_sig = QComboBox(); self.cmb_sig.setFont(f); gl.addWidget(self.cmb_sig, 1, 3)

        self.cmb_eps.currentTextChanged.connect(self.plot_full)
        self.cmb_sig.currentTextChanged.connect(self.plot_full)

        # 1c. 정보 라벨
        self.lbl_info = QLabel("Ready. Load a CSV file."); self.lbl_info.setFont(font_small()) # <-- font_small() 유지
        gl.addWidget(self.lbl_info, 2, 0, 1, 4)

        # 1d. 편집 버튼
        self.btn_set_start = QPushButton("Set as Start"); self.btn_set_start.setFont(f)
        self.btn_set_start.clicked.connect(self.set_start_point)
        gl.addWidget(self.btn_set_start, 3, 0, 1, 2)

        self.btn_reset = QPushButton("Reset Data"); self.btn_reset.setFont(f)
        self.btn_reset.clicked.connect(self.reset_data)
        gl.addWidget(self.btn_reset, 3, 2, 1, 2)

        self.btn_del_in = QPushButton("Delete Inside Range"); self.btn_del_in.setFont(f)
        self.btn_del_in.clicked.connect(self.delete_inside)
        gl.addWidget(self.btn_del_in, 4, 0, 1, 2)

        self.btn_del_out = QPushButton("Delete Outside Range (Crop)"); self.btn_del_out.setFont(f)
        self.btn_del_out.clicked.connect(self.delete_outside)
        gl.addWidget(self.btn_del_out, 4, 2, 1, 2)
        
        self.btn_export = QPushButton("Export Processed CSV"); self.btn_export.setFont(f)
        self.btn_export.clicked.connect(self.export_csv)
        gl.addWidget(self.btn_export, 5, 0, 1, 4)

        # --- 2. 그래프 영역 ---
        fig = Figure(figsize=(6, 5), dpi=100)
        self.ax = fig.add_subplot(111)
        self.canvas = ZoomableCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)

        # --- 3. 전체 레이아웃 ---
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6); root.setSpacing(6)
        root.addWidget(ctrl, stretch=0)
        root.addWidget(self.toolbar, stretch=0)
        root.addWidget(self.canvas, stretch=1)

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path: return
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
        self.cmb_eps.clear(); self.cmb_sig.clear()
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
        self.ax.plot(x_orig, y_orig, color=SK_GRAY, lw=1.0, ls='--', marker='.', markersize=2, label="Original")

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
        if self.clicked_point_marker:
            try: self.clicked_point_marker.remove()
            except Exception: pass
            self.clicked_point_marker = None
        self.clicked_point_coords = None

    def _init_span_selector(self, ax):
        if self.selector is not None:
            try: self.selector.disconnect_events()
            except Exception: pass
            self.selector = None
        
        self.selector = SpanSelector(
            ax, self._on_select, "horizontal",
            minspan=0.0001, useblit=True,
            props=dict(facecolor=SK_BLUE, alpha=0.22, edgecolor=SK_BLUE),
            interactive=True, drag_from_anywhere=True,
            button=1 
        )
        self.canvas.draw_idle()

    def _set_click_point(self, x_val, y_val):
        if x_val is None or y_val is None:
            return
            
        if self.clicked_point_marker:
            try: self.clicked_point_marker.remove()
            except Exception: pass
        
        self.clicked_point_marker = self.ax.plot(x_val, y_val, 'x', color=SK_BLUE, markersize=10, mew=2)[0]
        self.canvas.draw_idle()
        
        self.clicked_point_coords = (x_val, y_val)
        self.lbl_info.setText(f"Start point selected at (X={x_val:.4f}, Y={y_val:.2f})")

    def _on_mouse_press(self, event):
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
            data_x1_new, data_y1_new = self.ax.transData.inverted().transform((pix_x1_new, pix_y1_new))

            data_dx = data_x1_new - x1_0
            data_dy = data_y1_new - y1_0

            self.ax.set_xlim(x1_0 + data_dx, x2_0 + data_dx)
            self.ax.set_ylim(y1_0 + data_dy, y2_0 + data_dy)
            
            self.canvas.draw_idle()

    def _on_mouse_release(self, event):
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
        self.clear_markers() 
        self.selected_range = (xmin, xmax)
        self.lbl_info.setText(f"Range selected from {xmin:.2f} to {xmax:.2f}")

    # --- 버튼 액션 ---

    def set_start_point(self):
        if self.df_processed is None:
            QMessageBox.warning(self, "No Data", "먼저 CSV 파일을 로드하세요.")
            return
        if self.clicked_point_coords is None:
            QMessageBox.warning(self, "No Point", "그래프를 클릭하여 시작점을 먼저 선택하세요.")
            return

        x_col_name = self.cmb_eps.currentText().strip()
        x_offset, y_offset = self.clicked_point_coords

        df = self.df_original.copy()
        df = df[df[x_col_name] >= x_offset].copy()
        df.reset_index(drop=True, inplace=True)

        self.df_processed = df
        self.plot_full()
        self.lbl_info.setText(f"Trimmed data before X={x_offset:.4f}. {len(df)} points remaining.")

    def delete_inside(self):
        if self.df_processed is None:
            QMessageBox.warning(self, "No Data", "먼저 CSV 파일을 로드하세요.")
            return
        if self.selected_range is None:
            QMessageBox.warning(self, "No Range", "그래프를 드래그하여 삭제할 범위를 선택하세요.")
            return

        x_col_name = self.cmb_eps.currentText().strip()
        min_x = self.selected_range[0]
        max_x = self.selected_range[1]

        df = self.df_processed.copy()
        mask = (df[x_col_name] < min_x) | (df[x_col_name] > max_x)
        self.df_processed = df[mask].copy()
        
        self.plot_full()
        self.lbl_info.setText(f"Deleted data inside range. {len(self.df_processed)} points remaining.")

    def delete_outside(self):
        if self.df_processed is None:
            QMessageBox.warning(self, "No Data", "먼저 CSV 파일을 로드하세요.")
            return
        if self.selected_range is None:
            QMessageBox.warning(self, "No Range", "그래프를 드래그하여 보존할 범위를 선택하세요.")
            return

        x_col_name = self.cmb_eps.currentText().strip()
        min_x = self.selected_range[0]
        max_x = self.selected_range[1]

        df = self.df_processed.copy()
        mask = (df[x_col_name] >= min_x) & (df[x_col_name] <= max_x)
        self.df_processed = df[mask].copy()
        
        self.plot_full()
        self.lbl_info.setText(f"Cropped data to range. {len(self.df_processed)} points remaining.")

    def reset_data(self):
        if self.df_original is None:
            QMessageBox.warning(self, "No Data", "로드된 원본 데이터가 없습니다.")
            return
            
        self.df_processed = self.df_original.copy()
        self.plot_full()
        self.lbl_info.setText("Data reset to original state.")
        
    def export_csv(self):
        if self.df_processed is None:
            QMessageBox.warning(self, "No Data", "내보낼 편집 데이터가 없습니다.")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "Save Processed CSV", "", "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
            
        try:
            self.df_processed.to_csv(path, index=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CSV:\n{e}")
            return
            
        QMessageBox.information(self, "Saved", f"Processed CSV saved to:\n{path}")


# ── Tab 3 (Multi compare; + manual fit range)
class TabMultiCompare(QWidget):
    SK_COLORS = SK_MULTI
    def __init__(self):
        super().__init__()

        f = font_big()
        self.utm_files = []; self.dic_files = []
        self.pairs = []
        self.datasets = []
        self.selector = None
        self.span = None; self.vlines = []
        self.ax_info = None

        # [Pan] 1. 초기화
        self._pan_info = {}

        ctrl = QGroupBox("Multi compare · Load & Settings"); ctrl.setFont(f)
        gl = QGridLayout(ctrl)

        self.btn_load_multi = QPushButton("Load multiple UTM + DIC")
        self.btn_load_multi.setToolTip("Select UTM files (multi) → then DIC files (multi)")
        self.btn_load_multi.clicked.connect(self.load_multiple_sets)
        gl.addWidget(self.btn_load_multi, 0,0)

        self.lbl_summary = QLabel("UTM: 0, DIC: 0, Pairs: 0")
        gl.addWidget(self.lbl_summary, 0,1,1,3)
        
        pair_label = QLabel("Pairs (label = UTM stem):")
        gl.addWidget(pair_label, 1, 0, 1, 2)

        self.btn_remove_pair = QPushButton("Remove Selected Pair")
        self.btn_remove_pair.clicked.connect(self._remove_selected_pair)
        self.btn_remove_pair.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.btn_remove_pair.setToolTip("Remove the currently selected pair from the list")
        gl.addWidget(self.btn_remove_pair, 1, 3, alignment=Qt.AlignRight) 

        self.list_pairs = QListWidget(); self.list_pairs.setMinimumHeight(40)
        
        self.list_pairs.currentRowChanged.connect(self._on_pair_selected)
        gl.addWidget(self.list_pairs, 2, 0, 1, 4)

        gl.addWidget(QLabel("Default merge tol (s):"), 3,0)
        self.tol_default = QDoubleSpinBox(); self.tol_default.setDecimals(3); self.tol_default.setSingleStep(0.005)
        self.tol_default.setRange(0.0, 10.0); self.tol_default.setValue(0.06); self.tol_default.setFont(f)
        gl.addWidget(self.tol_default, 3,1)

        gl.addWidget(QLabel("Per-curve tol (s):"), 3,2)
        self.tol_pair = QDoubleSpinBox(); self.tol_pair.setDecimals(3); self.tol_pair.setSingleStep(0.005)
        self.tol_pair.setRange(0.0, 10.0); self.tol_pair.setValue(0.06); self.tol_pair.setEnabled(False); self.tol_pair.setFont(f)
        self.tol_pair.valueChanged.connect(self._update_selected_pair_tol)
        gl.addWidget(self.tol_pair, 3,3)

        # [New] 항복점 계산 여부 체크박스 (기본값 True)
        self.chk_yield = QCheckBox("Calc YS (0.2%)")
        self.chk_yield.setChecked(True)
        gl.addWidget(self.chk_yield, 4, 0, 1, 2)

        gl.addWidget(QLabel("Geometry:"), 5,0)
        self.geom = GeometryInput()
        gl.addWidget(self.geom, 5,1,1,3)

        gl.addWidget(QLabel("Manual fit range (%):"), 6,0)
        self.start_box = QDoubleSpinBox(); self.start_box.setDecimals(4); self.start_box.setRange(0.0, 100.0)
        self.start_box.setSingleStep(0.01); self.start_box.setValue(0.0)
        gl.addWidget(self.start_box, 6,1)
        self.end_box = QDoubleSpinBox(); self.end_box.setDecimals(4); self.end_box.setRange(0.0, 100.0)
        self.end_box.setSingleStep(0.01); self.end_box.setValue(0.0)
        gl.addWidget(self.end_box, 6,2)
        self.btn_manual_fit = QPushButton("Fit by Range")
        self.btn_manual_fit.clicked.connect(self._manual_fit)
        gl.addWidget(self.btn_manual_fit, 6,3)

        self.btn_plot = QPushButton("Generate Multi Curve"); self.btn_plot.clicked.connect(self.plot_multi)
        
        # [New] 그래프 저장 버튼 추가
        self.btn_save_img_multi = QPushButton("Save Graph"); self.btn_save_img_multi.clicked.connect(self.save_graph)
        
        # 버튼들 오른쪽 정렬 레이아웃
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btn_plot)
        btn_layout.addWidget(self.btn_save_img_multi)
        gl.addLayout(btn_layout, 7, 0, 1, 4)

        fig = Figure(figsize=(6,4), dpi=110)
        self.canvas = ZoomableCanvas(fig); self.toolbar = NavigationToolbar(self.canvas, self)
        
        # [Pan] 2. 이벤트 연결
        self.canvas.mpl_connect('button_press_event', self._on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self._on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self._on_mouse_move)

        plot_v = QVBoxLayout(); plot_v.setContentsMargins(0,0,0,0); plot_v.addWidget(self.toolbar); plot_v.addWidget(self.canvas)
        plot_wrap = QWidget(); plot_wrap.setLayout(plot_v)

        top = QWidget(); top_v = QVBoxLayout(top); top_v.setContentsMargins(0,0,0,0); top_v.setSpacing(8); top_v.addWidget(ctrl)
        self.splitter = QSplitter(Qt.Vertical); self.splitter.addWidget(top); self.splitter.addWidget(plot_wrap)
        
        self.splitter.setChildrenCollapsible(False)
        
        self.splitter.setSizes([320, 900])

        root = QVBoxLayout(self); root.setContentsMargins(8,8,8,8); root.setSpacing(8); root.addWidget(self.splitter)

    # [Pan] 3. 이벤트 핸들러
    def _on_mouse_press(self, event):
        if self.toolbar.mode != "" or event.inaxes != self.canvas.figure.axes[0]: return
        if event.button == 3:
            ax = self.canvas.figure.axes[0]
            self._pan_info = {'active': True, 'start_x': event.x, 'start_y': event.y, 'start_xlim': ax.get_xlim(), 'start_ylim': ax.get_ylim()}
            if self.selector: self.selector.set_active(False)

    def _on_mouse_move(self, event):
        if self._pan_info.get('active'):
            ax = self.canvas.figure.axes[0]
            dx = event.x - self._pan_info['start_x']
            dy = event.y - self._pan_info['start_y']
            x1, x2 = self._pan_info['start_xlim']; y1, y2 = self._pan_info['start_ylim']
            pix_x, pix_y = ax.transData.transform((x1, y1))
            pix_x -= dx; pix_y -= dy
            new_x, new_y = ax.transData.inverted().transform((pix_x, pix_y))
            ddx = new_x - x1; ddy = new_y - y1
            ax.set_xlim(x1+ddx, x2+ddx); ax.set_ylim(y1+ddy, y2+ddy)
            self.canvas.draw_idle()

    def _on_mouse_release(self, event):
        if event.button == 3:
            self._pan_info = {'active': False}
            if self.selector: self.selector.set_active(True)
            self.canvas.draw_idle()

    def _remove_selected_pair(self):
        row = self.list_pairs.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a pair from the list to remove.")
            return

        if 0 <= row < len(self.pairs):
            del self.pairs[row]
            self._refresh_pair_list()
            new_count = len(self.pairs)
            if new_count > 0:
                new_row = min(row, new_count - 1)
                self.list_pairs.setCurrentRow(new_row)

    # ---------- load/pair ----------
    def load_multiple_sets(self):
        utm_files, _ = QFileDialog.getOpenFileNames(self, "Select multiple UTM CSVs", "", "CSV (*.csv)")
        if not utm_files: return
        dic_files, _ = QFileDialog.getOpenFileNames(self, "Select multiple DIC CSVs", "", "CSV (*.csv)")
        if not dic_files:
            QMessageBox.information(self, "Info", "DIC selection cancelled."); return
        self.utm_files = sorted(utm_files); self.dic_files = sorted(dic_files)
        base_pairs = self._guess_pairs(self.utm_files, self.dic_files)
        self.pairs = [{"utm": u, "dic": d, "label": label, "tol": self.tol_default.value()} for (u,d,label) in base_pairs]
        self._refresh_pair_list()
        if self.pairs:
            self.list_pairs.setCurrentRow(0)

    def _refresh_pair_list(self):
        self.list_pairs.clear()
        for i, p in enumerate(self.pairs, 1):
            self.list_pairs.addItem(f"{i:02d}. {p['label']} | tol={p['tol']:.3f}s | "
                                    f"UTM={os.path.basename(p['utm'])} / DIC={os.path.basename(p['dic'])}")
        self.lbl_summary.setText(f"UTM: {len(self.utm_files)}, DIC: {len(self.dic_files)}, Pairs: {len(self.pairs)}")
        self.tol_pair.setEnabled(False)

    def _on_pair_selected(self, row):
        if 0 <= row < len(self.pairs):
            self.tol_pair.blockSignals(True)
            self.tol_pair.setEnabled(True)
            self.tol_pair.setValue(float(self.pairs[row]["tol"]))
            self.tol_pair.blockSignals(False)
        else:
            self.tol_pair.setEnabled(False)

    def _update_selected_pair_tol(self, val):
        row = self.list_pairs.currentRow()
        if 0 <= row < len(self.pairs):
            self.pairs[row]["tol"] = float(val)
            self.list_pairs.item(row).setText(
                f"{row+1:02d}. {self.pairs[row]['label']} | tol={val:.3f}s | "
                f"UTM={os.path.basename(self.pairs[row]['utm'])} / DIC={os.path.basename(self.pairs[row]['dic'])}"
            )

    @staticmethod
    def _stem(p): return os.path.splitext(os.path.basename(p))[0]
    @staticmethod
    def _digits(s): return ''.join(ch for ch in s if ch.isdigit()) or None

    def _guess_pairs(self, utm_list, dic_list):
        pairs = []
        if not utm_list or not dic_list: return pairs
        utm_map = {self._digits(self._stem(u)): u for u in utm_list}
        dic_map = {self._digits(self._stem(d)): d for d in dic_list}
        keys = [k for k in utm_map if k and k in dic_map]; keys = sorted(keys, key=lambda x: int(x))
        for k in keys: pairs.append((utm_map[k], dic_map[k], f"sample{k}"))
        paired_utm = set(u for u,_,_ in pairs); paired_dic = set(d for _,d,_ in pairs)
        rem_utm = [u for u in utm_list if u not in paired_utm]; rem_dic = [d for d in dic_list if d not in paired_dic]
        stems_dic = {self._stem(d): d for d in rem_dic}
        for u in rem_utm[:]:
            s = self._stem(u)
            if s in stems_dic:
                pairs.append((u, stems_dic[s], s)); rem_utm.remove(u)
        for u, d in zip(sorted(rem_utm), sorted(rem_dic)):
            pairs.append((u, d, self._stem(u)))
        return sorted(pairs, key=lambda x: x[2])

    # ---------- helpers ----------
    def _clear_span(self):
        if getattr(self, "span", None) is not None:
            try: self.span.remove()
            except Exception: pass
            self.span = None
        for ln in getattr(self, "vlines", []):
            try: ln.remove()
            except Exception: pass
        self.vlines = []

    def _init_span_selector(self, ax):
        if self.selector is not None:
            try: self.selector.disconnect_events()
            except Exception: pass
            self.selector = None
        self.selector = SpanSelector(
            ax, self._on_select, "horizontal",
            minspan=0.0001, useblit=True,
            props=dict(facecolor="#00BCD4", alpha=0.22, edgecolor="#00ACC1"),
            interactive=True, drag_from_anywhere=True,
            button=1 
        )
        for attr in ("ignore_event_outside", "ignore_events_outside"):
            if hasattr(self.selector, attr): setattr(self.selector, attr, False)

    @staticmethod
    def _fit_slope(xs, ys):
        n = len(xs)
        if n >= 3:
            a, _ = np.polyfit(xs, ys, 1)
            return float(a)
        elif n == 2:
            if xs[1] == xs[0]: return np.nan
            return float((ys[1] - ys[0])/(xs[1] - xs[0]))
        return np.nan

    def _ensure_side_panel(self, fig):
        # [유지] Margin 설정 (top=1.0, bottom=0.2)
        fig.subplots_adjust(top=1.0, bottom=0.2, right=0.65)
        
        if self.ax_info is None or self.ax_info not in fig.axes:
            self.ax_info = fig.add_axes([0.67, 0.12, 0.32, 0.76])
        ax = self.ax_info
        ax.clear()
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_frame_on(False)
        ax.set_facecolor("none")
        ax.set_title("E (Modulus) & UTS", color="black", fontsize=12, fontweight="bold", pad=4)

    # ---------- main plot ----------
    def plot_multi(self):
        if not self.pairs:
            QMessageBox.information(self, "Info", "Load UTM/DIC files first."); return

        self.datasets = []; self._clear_span()
        
        try:
            w_mm, t_mm, _ = self.geom.get()
            if w_mm * t_mm == 0:
                 QMessageBox.warning(self, "Error", "Geometry(면적)는 0이 될 수 없습니다."); return
            A = (w_mm*1e-3) * (t_mm*1e-3)
        except ValueError:
            return

        fig = self.canvas.figure; fig.clear()
        ax = fig.add_subplot(111)

        #  항복점 계산 여부 확인
        calc_yield = self.chk_yield.isChecked()

        for idx, p in enumerate(self.pairs):
            udf = pd.read_csv(utm_path, chunksize=10000)
            utm_path, dic_path, tol = p["utm"], p["dic"], float(p["tol"])
            label = p["label"]
            try:
                udf = safe_read_csv(utm_path); udf.columns = [c.strip() for c in udf.columns]
                ddf = safe_read_csv(dic_path); ddf.columns = [c.strip() for c in ddf.columns]
                
                td_col_name = ddf.columns[0]
                if pd.api.types.is_numeric_dtype(ddf[td_col_name]):
                    ddf[td_col_name] = ddf[td_col_name] - ddf[td_col_name].iloc[0]

                tu_col_name = udf.columns[0]
                if pd.api.types.is_numeric_dtype(udf[tu_col_name]):
                    udf[tu_col_name] = udf[tu_col_name] - udf[tu_col_name].iloc[0]


                tu = udf.columns[0]
                nums_u = udf.select_dtypes(include='number').columns.tolist()
                load_cols = [c for c in nums_u if c != tu and ("load" in c.lower() or "force" in c.lower())] or [c for c in nums_u if c != tu]
                if not load_cols: continue
                lc = load_cols[0]
                
                td = ddf.columns[0]
                nums_d = ddf.select_dtypes(include='number').columns.tolist()
                dic_cols = [c for c in nums_d if c != td and any(k in c.lower() for k in ["strain","ε","exx","eyy","e_"])] or [c for c in nums_d if c != td]
                if not dic_cols: continue
                sx = dic_cols[0]

                udf = udf.sort_values(tu); ddf = ddf.sort_values(td)
                m = pd.merge_asof(udf[[tu, lc]], ddf[[td, sx]], left_on=tu, right_on=td,
                                  direction="nearest", tolerance=tol).dropna(subset=[sx])
                
                if m.empty:
                    print(f"[WARN] Merge result is empty for {label}. Check time columns or tolerance.")
                    continue

                eps_eng  = m[sx].astype(float) / 100.0
                eps_true = np.log1p(eps_eng)
                sig_eng  = (m[lc] - m[lc].iloc[0]) / A / 1e6
                sig_true = sig_eng * (1.0 + eps_eng)

                # [수정됨] Auto logic 삭제 -> 항상 0점 보정만 수행
                eps_use = (eps_true - eps_true.iloc[0]).values
                sig_use = (sig_true - sig_true.iloc[0]).values

                color = self.SK_COLORS[idx % len(self.SK_COLORS)]
                ax.plot(eps_use*100.0, sig_use, '-', color=color, label=label)

                uts = float(np.nanmax(sig_use))
                
                # [New] 항복 강도 계산 및 표시 (다중 그래프용)
                ys_val = None
                if calc_yield:
                    ys, ys_idx, _ = calculate_yield_strength(eps_use, sig_use)
                    if ys is not None:
                        ys_val = ys
                        # 해당 곡선과 동일한 색상(color)으로 마커 표시
                        ax.plot(eps_use[ys_idx]*100.0, ys, 'o', color=color, markersize=6, markeredgecolor='white')

                self.datasets.append({"label": label, "color": color,
                                      "eps": eps_use, "sig": sig_use, "uts": uts, "ys": ys_val}) # ys 정보 추가
            except Exception as e:
                print(f"[WARN] {os.path.basename(utm_path)} / {os.path.basename(dic_path)} : {e}")

        ax.set_xlabel("True Strain (%)"); ax.set_ylabel("True Stress (MPa)")
        self._ensure_side_panel(fig)
        
        # [Modified] 정보 패널에 YS도 같이 전달
        self._render_info_panel(rows=[(d["label"], d["color"], None, d["uts"], d.get("ys")) for d in self.datasets])

        self.canvas.draw()
        if self.datasets: self._init_span_selector(ax)

    # ---------- side panel ----------
    def _render_info_panel(self, rows):
        self._ensure_side_panel(self.canvas.figure)
        ax = self.ax_info

        y = 0.90

        ax.clear()
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_frame_on(False)
        ax.set_facecolor("none")
        
        try:
            show_ys = self.chk_yield.isChecked()
        except AttributeError:
            show_ys = True

        title_str = "Properties (E, UTS, YS)" if show_ys else "Properties (E, UTS)"
        
        ax.set_title(title_str, color="black",
              fontsize=13, fontweight="bold", pad=4)

        y = 0.92
        # row: (label, color, E_mpa, uts, ys) -> ys 추가됨
        for row_data in rows:
            # 언팩킹 (가변 길이 대응)
            label, color, E_mpa, uts = row_data[:4]
            ys_val = row_data[4] if len(row_data) > 4 else None

            e_txt = "E=–" if (E_mpa is None or not np.isfinite(E_mpa)) else f"E={E_mpa/1000.0:.3f} GPa"
            u_txt = f"UTS={uts:.1f}"
            
            # [Modified] 체크박스 상태에 따라 정보 텍스트 분기
            if show_ys:
                y_txt = f"YS={ys_val:.1f}" if ys_val is not None else "YS=–"
                info_str = f"{e_txt} | {u_txt} | {y_txt} MPa"
            else:
                info_str = f"{e_txt} | {u_txt} MPa"

            ax.text(0.0, y, f"{label}", transform=ax.transAxes,
                    ha="left", va="center", fontsize=11,
                    color=color, fontweight="bold")
            ax.text(0.0, y-0.055, info_str, transform=ax.transAxes,
                    ha="left", va="center", fontsize=10.5, color="#333")
            y -= 0.13

        ax.set_xlim(0,1); ax.set_ylim(0,1)
        self.canvas.draw_idle()

    # ---------- drag selection ----------
    def _on_select(self, x_min, x_max):
        if not self.datasets or x_max <= x_min: return
        if (x_max - x_min) < 0.0001:
            pad = 0.00005; x_min -= pad; x_max += pad

        eps_min = x_min/100.0; eps_max = x_max/100.0

        self._clear_span()
        ax = self.canvas.figure.axes[0]
        self.span = ax.axvspan(x_min, x_max, color="#00BCD4", alpha=0.22, zorder=0.5)
        self.vlines = [
            ax.axvline(x_min, color="#00ACC1", lw=2, zorder=1.5),
            ax.axvline(x_max, color="#00ACC1", lw=2, zorder=1.5),
        ]

        rows = []
        for d in self.datasets:
            eps = d["eps"]; sig = d["sig"]
            msk = (eps >= eps_min) & (eps <= eps_max)
            xs = eps[msk]; ys = sig[msk]
            E_mpa = self._fit_slope(xs, ys)
            # 드래그 시에도 YS 정보 유지해서 전달
            rows.append((d["label"], d["color"], E_mpa, d["uts"], d.get("ys")))

        self._render_info_panel(rows=rows)

    # ---------- manual fit by input (NEW) ----------
    def _manual_fit(self):
        if not self.datasets:
            QMessageBox.information(self, "Info", "Generate curves first."); return
        x_min = float(self.start_box.value()); x_max = float(self.end_box.value())
        if x_max <= x_min:
            QMessageBox.warning(self, "Error", "End (%) must be greater than Start (%)."); return

        self._clear_span()
        ax = self.canvas.figure.axes[0]
        self.span = ax.axvspan(x_min, x_max, color="#00BCD4", alpha=0.22, zorder=0.5)
        self.vlines = [
            ax.axvline(x_min, color="#00ACC1", lw=2, zorder=1.5),
            ax.axvline(x_max, color="#00ACC1", lw=2, zorder=1.5),
        ]

        eps_min = x_min/100.0; eps_max = x_max/100.0
        rows = []
        for d in self.datasets:
            eps = d["eps"]; sig = d["sig"]
            msk = (eps >= eps_min) & (eps <= eps_max)
            xs = eps[msk]; ys = sig[msk]
            E_mpa = self._fit_slope(xs, ys) if len(xs) >= 2 else np.nan
            rows.append((d["label"], d["color"], E_mpa, d["uts"], d.get("ys")))
        self._render_info_panel(rows=rows)
        self.canvas.draw_idle()

    # [New] Multi Compare용 그래프 저장 함수
    def save_graph(self):
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
            QMessageBox.information(self, "Saved", f"Graph saved to:\n{os.path.basename(path)}")
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Failed to save graph:\n{e}")


# ── Main
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SS Curve Generator / Modulus Fitting / Multi compare")
        self.resize(1600, 980)

        tabs = QTabWidget()
        tabs.addTab(TabDICUTM(), "SS Curve Generator")
        tabs.addTab(TabPreprocessor(), "CSV Preprocessor")
        tabs.addTab(TabMultiCompare(), "Multi compare")
        root = QVBoxLayout(self); root.setContentsMargins(6,6,6,6); root.setSpacing(6); root.addWidget(tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    try:
        app_font = QFont("Pretendard", 13, QFont.DemiBold)
    except Exception:
        app_font = QFont("Arial", 13, QFont.Bold)
    app.setFont(app_font)

    w = MainWindow(); w.show(); sys.exit(app.exec_())