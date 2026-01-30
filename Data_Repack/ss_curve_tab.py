"""
SS Curve Generator Tab
단일 UTM + DIC 파일로부터 응력-변형률 곡선 생성
"""

import os
import numpy as np
import pandas as pd
import matplotlib as mpl
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QComboBox, QPushButton, QFileDialog, QMessageBox, 
    QDoubleSpinBox, QCheckBox, QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)

from .utils import (
    safe_read_csv, font_big, SK_RED, calculate_yield_strength,
    is_likely_strain_column, is_likely_load_column
)
from .geometry_input import GeometryInput

# Matplotlib 스타일
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


class ZoomableCanvas(FigureCanvas):
    """마우스 휠로 줌 가능한 캔버스"""
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


class TabDICUTM(QWidget):
    """SS Curve Generator Tab"""
    
    def __init__(self):
        super().__init__()
        f = font_big()
        self.udf = None
        self.ddf = None
        self.out_df = None
        
        self._pan_info = {}

        # ===== Control Panel =====
        ctrl = QGroupBox("Load · Settings")
        ctrl.setFont(f)
        gl = QVBoxLayout(ctrl)

        # UTM 파일
        utm_row = QHBoxLayout()
        self.btn_utm = QPushButton("Load UTM CSV")
        self.btn_utm.setFont(f)
        self.btn_utm.clicked.connect(self.load_utm)
        self.lbl_utm = QLabel("UTM: -")
        utm_row.addWidget(self.btn_utm)
        utm_row.addWidget(self.lbl_utm, 1)
        gl.addLayout(utm_row)

        # DIC 파일
        dic_row = QHBoxLayout()
        self.btn_dic = QPushButton("Load DIC CSV")
        self.btn_dic.setFont(f)
        self.btn_dic.clicked.connect(self.load_dic)
        self.lbl_dic = QLabel("DIC: -")
        dic_row.addWidget(self.btn_dic)
        dic_row.addWidget(self.lbl_dic, 1)
        gl.addLayout(dic_row)

        # 컬럼 선택
        col_row = QHBoxLayout()
        col_row.addWidget(QLabel("UTM Load (N):"))
        self.cmb_load = QComboBox()
        self.cmb_load.setEnabled(False)
        self.cmb_load.setFont(f)
        col_row.addWidget(self.cmb_load)
        
        col_row.addWidget(QLabel("DIC Strain (%):"))
        self.cmb_dic = QComboBox()
        self.cmb_dic.setEnabled(False)
        self.cmb_dic.setFont(f)
        col_row.addWidget(self.cmb_dic)
        gl.addLayout(col_row)

        # Tolerance & Yield
        opt_row = QHBoxLayout()
        opt_row.addWidget(QLabel("Merge tol (s):"))
        self.tol = QDoubleSpinBox()
        self.tol.setDecimals(3)
        self.tol.setSingleStep(0.005)
        self.tol.setRange(0.0, 10.0)
        self.tol.setValue(0.06)
        self.tol.setFont(f)
        opt_row.addWidget(self.tol)
        
        self.chk_yield = QCheckBox("Calc Yield Strength (0.2%)")
        self.chk_yield.setChecked(True)
        opt_row.addWidget(self.chk_yield)
        gl.addLayout(opt_row)

        # Geometry
        geom_row = QHBoxLayout()
        geom_row.addWidget(QLabel("Geometry:"))
        self.geom = GeometryInput()
        geom_row.addWidget(self.geom, 1)
        gl.addLayout(geom_row)

        # Buttons
        btn_row = QHBoxLayout()
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

        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_plot)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_save_img)
        gl.addLayout(btn_row)

        # Results
        res = QGroupBox("Results")
        res.setFont(f)
        h = QHBoxLayout(res)
        self.lbl_uts = QLabel("UTS: - (MPa) | YS: - (MPa)")
        h.addWidget(self.lbl_uts)
        h.addStretch(1)

        # ===== Graph =====
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

        # ===== Layout =====
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

            lc = self.cmb_load.currentText()
            sx = self.cmb_dic.currentText()
            
            # 컬럼 선택 검증
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
