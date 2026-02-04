"""
Multi Compare Tab
여러 UTM+DIC 쌍을 비교
"""

import os
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QFileDialog, QMessageBox, QDoubleSpinBox,
    QSplitter, QListWidget, QInputDialog
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.widgets import SpanSelector

from .utils import (
    safe_read_csv, font_big, SK_MULTI, 
    calculate_yield_strength, is_likely_strain_column, is_likely_load_column
)
from .geometry_input import GeometryInput


class TabMultiCompare(QWidget):
    """Multi Compare Tab"""
    
    SK_COLORS = SK_MULTI
    
    def __init__(self, lang_manager=None):
        super().__init__()

        # ===== LanguageManager 저장 =====
        self.lang_manager = lang_manager

        f = font_big()
        self.utm_files = []
        self.dic_files = []
        self.pairs = []
        self.datasets = []

        # ===== Control Panel =====
        self.ctrl = QGroupBox("Multi compare · Load & Settings")
        self.ctrl.setFont(f)
        gl = QVBoxLayout(self.ctrl)

        # Load buttons
        load_row = QHBoxLayout()
        self.btn_load_multi = QPushButton("Load Multiple UTM + DIC")
        self.btn_load_multi.setToolTip("Select UTM files (multi) → then DIC files (multi)")
        self.btn_load_multi.clicked.connect(self.load_multiple_sets)
        load_row.addWidget(self.btn_load_multi)

        self.lbl_summary = QLabel("UTM: 0, DIC: 0, Pairs: 0")
        load_row.addWidget(self.lbl_summary)
        gl.addLayout(load_row)
        
        # Pair list label
        self.pair_list_label = QLabel("Pairs (label = auto-extracted):")  # ← 저장
        gl.addWidget(self.pair_list_label)

        # Edit buttons
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
        self.btn_remove_pair.setToolTip("Remove the currently selected pair")
        
        edit_btn_layout.addWidget(self.btn_add_single)
        edit_btn_layout.addWidget(self.btn_edit_label)
        edit_btn_layout.addWidget(self.btn_remove_pair)
        edit_btn_layout.addStretch()
        gl.addLayout(edit_btn_layout)

        # Pair list
        self.list_pairs = QListWidget()
        self.list_pairs.setMinimumHeight(80)
        self.list_pairs.currentRowChanged.connect(self._on_pair_selected)
        gl.addWidget(self.list_pairs)

        # Tolerance settings
        tol_row = QHBoxLayout()
        self.default_tol_label = QLabel("Default merge tol (s):")  # ← 저장
        tol_row.addWidget(self.default_tol_label)
        self.tol_default = QDoubleSpinBox()
        self.tol_default.setDecimals(3)
        self.tol_default.setSingleStep(0.005)
        self.tol_default.setRange(0.0, 10.0)
        self.tol_default.setValue(0.06)
        self.tol_default.setFont(f)
        tol_row.addWidget(self.tol_default)

        self.per_curve_tol_label = QLabel("Per-curve tol (s):")  # ← 저장
        tol_row.addWidget(self.per_curve_tol_label)
        self.tol_pair = QDoubleSpinBox()
        self.tol_pair.setDecimals(3)
        self.tol_pair.setSingleStep(0.005)
        self.tol_pair.setRange(0.0, 10.0)
        self.tol_pair.setValue(0.06)
        self.tol_pair.setEnabled(False)
        self.tol_pair.setFont(f)
        self.tol_pair.valueChanged.connect(self._update_selected_pair_tol)
        tol_row.addWidget(self.tol_pair)
        gl.addLayout(tol_row)

        # Geometry
        geom_row = QHBoxLayout()
        self.geometry_label = QLabel("Geometry:")  # ← 저장
        geom_row.addWidget(self.geometry_label)
        self.geom = GeometryInput(lang_manager=lang_manager)
        geom_row.addWidget(self.geom, 1)
        gl.addLayout(geom_row)

        # Manual fit range
        fit_row = QHBoxLayout()
        self.fit_range_label = QLabel("Manual fit range (%):")  # ← 저장
        fit_row.addWidget(self.fit_range_label)
        self.start_box = QDoubleSpinBox()
        self.start_box.setDecimals(4)
        self.start_box.setRange(0.0, 100.0)
        self.start_box.setSingleStep(0.01)
        self.start_box.setValue(0.0)
        fit_row.addWidget(self.start_box)
        
        self.end_box = QDoubleSpinBox()
        self.end_box.setDecimals(4)
        self.end_box.setRange(0.0, 100.0)
        self.end_box.setSingleStep(0.01)
        self.end_box.setValue(0.0)
        fit_row.addWidget(self.end_box)
        
        self.btn_manual_fit = QPushButton("Fit by Range")
        self.btn_manual_fit.clicked.connect(self._manual_fit)
        fit_row.addWidget(self.btn_manual_fit)
        gl.addLayout(fit_row)

        # Action buttons
        btn_row = QHBoxLayout()
        self.btn_plot = QPushButton("Generate Multi Curve")
        self.btn_plot.clicked.connect(self.plot_multi)
        
        self.btn_save_img_multi = QPushButton("Save Graph")
        self.btn_save_img_multi.clicked.connect(self.save_graph)
        
        btn_row.addStretch()
        btn_row.addWidget(self.btn_plot)
        btn_row.addWidget(self.btn_save_img_multi)
        gl.addLayout(btn_row)

        # ===== Graph =====
        fig = Figure(figsize=(6, 4), dpi=110)
        self.canvas = FigureCanvas(fig)
        self.canvas.setFocusPolicy(Qt.StrongFocus)
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

        # ===== Splitter =====
        top = QWidget()
        top.setLayout(gl)
        
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(top)
        self.splitter.addWidget(plot_wrap)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setSizes([400, 600])

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)
        root.addWidget(self.splitter)

        # ===== 추가 변수 초기화 =====
        self.selector = None
        self.span = None
        self.vlines = []
        self.ax_info = None
        self._pan_info = {}
        self.selected_range = None

    def _on_pair_selected(self, row):
        """리스트에서 Pair 선택 시"""
        if 0 <= row < len(self.pairs):
            self.tol_pair.blockSignals(True)
            self.tol_pair.setEnabled(True)
            self.tol_pair.setValue(float(self.pairs[row]["tol"]))
            self.tol_pair.blockSignals(False)
        else:
            self.tol_pair.setEnabled(False)

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
        """파일명 추출"""
        return os.path.splitext(os.path.basename(p))[0]
    
    @staticmethod
    def _extract_common_prefix(utm_stem, dic_stem):
        """공통 접두사 추출"""
        # 1단계: 문자 단위
        common = []
        for u_char, d_char in zip(utm_stem, dic_stem):
            if u_char == d_char:
                common.append(u_char)
            else:
                break
        
        common_prefix = ''.join(common).rstrip('_-. ')
        
        # 2단계: 단어 단위
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
        
        # 3단계: 숫자만
        if len(common_prefix) < 2:
            utm_digits = ''.join(ch for ch in utm_stem if ch.isdigit())
            dic_digits = ''.join(ch for ch in dic_stem if ch.isdigit())
            
            if utm_digits and utm_digits == dic_digits:
                common_prefix = f"sample{utm_digits}"
            else:
                common_prefix = utm_stem
                for suffix in ['_load', '_force', '_utm', '_test', '_data']:
                    if common_prefix.lower().endswith(suffix):
                        common_prefix = common_prefix[:-len(suffix)]
                        break
        
        return common_prefix if common_prefix else utm_stem

    def _ensure_unique_label(self, base_label):
        """라벨 중복 방지"""
        existing_labels = {p["label"] for p in self.pairs}
        
        if base_label not in existing_labels:
            return base_label
        
        counter = 1
        while f"{base_label}_{counter}" in existing_labels:
            counter += 1
        
        return f"{base_label}_{counter}"

    def _add_single_pair(self):
        """하나의 UTM + DIC 파일 쌍을 수동으로 추가"""
        tr = self.lang_manager.translate if self.lang_manager else lambda x: x
        
        utm_file, _ = QFileDialog.getOpenFileName(
            self, 
            tr("data.select_utm"),  # ← 번역 키 추가 필요
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        if not utm_file:
            return
        
        dic_file, _ = QFileDialog.getOpenFileName(
            self, 
            tr("data.select_dic"),  # ← 번역 키 추가 필요
            "", 
            "CSV Files (*.csv);;All Files (*)"
        )
        if not dic_file:
            QMessageBox.information(self, tr("msg.cancelled"), tr("msg.dic_cancelled"))
            return
        
        # 동일 파일 방지
        if utm_file == dic_file:
            QMessageBox.warning(
                self,
                tr("msg.invalid_selection"),
                tr("msg.files_must_different")
            )
            return
        
        utm_stem = self._stem(utm_file)
        dic_stem = self._stem(dic_file)
        
        # 파일명 동일 경고
        if utm_stem == dic_stem:
            reply = QMessageBox.question(
                self,
                tr("msg.same_filename_warning"),
                tr("msg.same_filename_desc").format(utm_stem),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        default_label = self._extract_common_prefix(utm_stem, dic_stem)
        default_label = self._ensure_unique_label(default_label)
        
        label, ok = QInputDialog.getText(
            self, 
            tr("data.enter_pair_label"),
            tr("data.label_for_pair"),
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
                    tr("msg.duplicate_label"),
                    tr("msg.duplicate_label_desc").format(label)
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
            tr("msg.pair_added"),
            tr("msg.pair_added_desc").format(
                label, 
                os.path.basename(utm_file), 
                os.path.basename(dic_file)
            )
        )
   
    def _edit_selected_label(self):
        """선택된 Pair의 라벨 수정"""
        tr = self.lang_manager.translate if self.lang_manager else lambda x: x
        
        row = self.list_pairs.currentRow()
        if row < 0:
            QMessageBox.warning(self, tr("msg.no_selection"), tr("msg.select_pair"))
            return
        
        if 0 <= row < len(self.pairs):
            current_label = self.pairs[row]["label"]
            new_label, ok = QInputDialog.getText(
                self, 
                tr("data.edit_label"),
                tr("data.enter_new_label"),
                text=current_label
            )
            
            if ok and new_label.strip():
                existing_labels = {
                    p["label"] for i, p in enumerate(self.pairs) if i != row
                }
                
                final_label = new_label.strip()
                if final_label in existing_labels:
                    QMessageBox.warning(
                        self,
                        tr("msg.duplicate_label"),
                        tr("msg.choose_different_name")
                    )
                    return
                
                self.pairs[row]["label"] = final_label
                self._refresh_pair_list()
                self.list_pairs.setCurrentRow(row)
    
    def _remove_selected_pair(self):
        """선택된 Pair 삭제"""
        tr = self.lang_manager.translate if self.lang_manager else lambda x: x
        
        row = self.list_pairs.currentRow()
        if row < 0:
            QMessageBox.warning(self, tr("msg.no_selection"), tr("msg.select_pair"))
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
                tr("msg.pair_removed"),
                tr("msg.pair_removed_desc").format(removed_pair['label'])
            )

    def load_multiple_sets(self):
        """여러 UTM+DIC 파일을 한 번에 로드"""
        tr = self.lang_manager.translate if self.lang_manager else lambda x: x
        
        utm_files, _ = QFileDialog.getOpenFileNames(
            self, 
            tr("data.select_multiple_utm"),
            "", 
            "CSV (*.csv)"
        )
        if not utm_files: 
            return
        
        dic_files, _ = QFileDialog.getOpenFileNames(
            self, 
            tr("data.select_multiple_dic"),
            "", 
            "CSV (*.csv)"
        )
        if not dic_files:
            QMessageBox.information(self, tr("msg.info"), tr("msg.dic_cancelled"))
            return
        
        self.utm_files = sorted(utm_files)
        self.dic_files = sorted(dic_files)
        
        base_pairs = self._guess_pairs(self.utm_files, self.dic_files)
        
        # 동일 파일 쌍 필터링
        valid_pairs = []
        invalid_count = 0
        
        for (u, d, label) in base_pairs:
            if u == d or self._stem(u) == self._stem(d):
                invalid_count += 1
                continue
            valid_pairs.append((u, d, label))
        
        if invalid_count > 0:
            QMessageBox.warning(
                self,
                tr("msg.invalid_pairs"),
                tr("msg.invalid_pairs_desc").format(invalid_count)
            )
        
        if not valid_pairs:
            QMessageBox.warning(self, tr("msg.no_valid_pairs"), tr("msg.no_valid_pairs_found"))
            return
        
        # 중복 라벨 방지
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
            tr("msg.load_complete"),
            tr("msg.pairs_loaded").format(len(self.pairs))
        )

    def _refresh_pair_list(self):
        """Pair 리스트 UI 갱신"""
        tr = self.lang_manager.translate if self.lang_manager else lambda x: x
        
        self.list_pairs.clear()
        for i, p in enumerate(self.pairs, 1):
            # ===== 번역된 형식 사용 =====
            item_text = tr("data.pair_item_format").format(
                i, 
                p['label'], 
                p['tol']
            )
            self.list_pairs.addItem(item_text)
        
        self.lbl_summary.setText(
            tr("data.summary_format").format(
                len(self.utm_files), 
                len(self.dic_files), 
                len(self.pairs)
            )
        )
        self.tol_pair.setEnabled(False)

    def _render_info_panel(self, rows):
        """사이드 패널 정보 표시"""
        tr = self.lang_manager.translate if self.lang_manager else lambda x: x
        
        self._ensure_side_panel(self.canvas.figure)
        ax = self.ax_info

        ax.clear()
        ax.set_title(tr("data.properties"), color="black", fontsize=13, fontweight="bold")

        y = 0.92
        for row_data in rows:
            label, color, E_mpa, uts = row_data[:4]
            ys_val = row_data[4] if len(row_data) > 4 else None

            # ===== 번역 적용 =====
            if E_mpa is None or not np.isfinite(E_mpa):
                e_txt = tr("data.e_value_na")
            else:
                e_txt = tr("data.e_value").format(E_mpa / 1000.0)
            
            u_txt = tr("data.uts_value").format(uts)
            
            if ys_val:
                y_txt = tr("data.ys_value").format(ys_val)
            else:
                y_txt = tr("data.ys_value_na")
            
            info_str = f"{e_txt} | {u_txt} | {y_txt}"

            ax.text(0.0, y, f"{label}", transform=ax.transAxes, ha="left", fontsize=11, color=color, fontweight="bold")
            ax.text(0.0, y - 0.055, info_str, transform=ax.transAxes, ha="left", fontsize=10.5, color="#333")
            y -= 0.13

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        self.canvas.draw_idle()

    def _update_selected_pair_tol(self, val):
        """선택된 Pair의 tolerance 값 업데이트"""
        row = self.list_pairs.currentRow()
        if 0 <= row < len(self.pairs):
            self.pairs[row]["tol"] = float(val)
            self._refresh_pair_list()
            self.list_pairs.setCurrentRow(row)

    def _guess_pairs(self, utm_list, dic_list):
        """파일 목록으로부터 자동 쌍 추정"""
        pairs = []
        if not utm_list or not dic_list: 
            return pairs
        
        # 숫자 기반 매칭
        def extract_digits(s):
            return ''.join(ch for ch in s if ch.isdigit()) or None
        
        utm_digit_map = {extract_digits(self._stem(u)): u for u in utm_list if extract_digits(self._stem(u))}
        dic_digit_map = {extract_digits(self._stem(d)): d for d in dic_list if extract_digits(self._stem(d))}
        
        digit_keys = sorted([k for k in utm_digit_map if k in dic_digit_map], key=lambda x: int(x))
        
        for k in digit_keys:
            label = self._extract_common_prefix(self._stem(utm_digit_map[k]), self._stem(dic_digit_map[k]))
            pairs.append((utm_digit_map[k], dic_digit_map[k], label))
        
        # stem 완전 일치
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
        
        # 순서대로
        for u, d in zip(sorted(rem_utm), sorted(rem_dic)):
            label = self._extract_common_prefix(self._stem(u), self._stem(d))
            pairs.append((u, d, label))
        
        return sorted(pairs, key=lambda x: x[2])

    def _clear_span(self):
        """범위 선택 표시 제거"""
        if self.span:
            try: 
                self.span.remove()
            except: 
                pass
            self.span = None
        for ln in self.vlines:
            try: 
                ln.remove()
            except: 
                pass
        self.vlines = []

    def _init_span_selector(self, ax):
        """SpanSelector 초기화"""
        if self.selector:
            try: 
                self.selector.disconnect_events()
            except: 
                pass
            self.selector = None
        
        self.selector = SpanSelector(
            ax, 
            self._on_select, 
            "horizontal",
            minspan=0.0001, 
            useblit=True,
            props=dict(facecolor="#00BCD4", alpha=0.22),
            interactive=True, 
            drag_from_anywhere=True,
            button=1 
        )

    @staticmethod
    def _fit_slope(xs, ys):
        """선형 피팅"""
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
        """사이드 패널 생성"""
        fig.subplots_adjust(top=1.0, bottom=0.2, right=0.65)
        
        if self.ax_info is None or self.ax_info not in fig.axes:
            self.ax_info = fig.add_axes([0.67, 0.12, 0.32, 0.76])
        ax = self.ax_info
        ax.clear()
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)
        ax.set_facecolor("none")

    def plot_multi(self):
        """여러 곡선을 한 번에 플롯"""
        if not self.pairs:
            QMessageBox.information(self, "Info", "Load files first.")
            return

        self.datasets = []
        self._clear_span()
        
        try:
            w_mm, t_mm, _ = self.geom.get()
            if w_mm * t_mm == 0:
                 QMessageBox.warning(self, "Error", "Geometry cannot be 0.")
                 return
            A = (w_mm * 1e-3) * (t_mm * 1e-3)
        except ValueError:
            return

        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        for idx, p in enumerate(self.pairs):
            utm_path, dic_path, tol = p["utm"], p["dic"], float(p["tol"])
            label = p["label"]
            try:
                udf = safe_read_csv(utm_path)
                udf.columns = [c.strip() for c in udf.columns]
                
                ddf = safe_read_csv(dic_path)
                ddf.columns = [c.strip() for c in ddf.columns]
                
                # Time zero
                td_col = ddf.columns[0]
                if pd.api.types.is_numeric_dtype(ddf[td_col]):
                    ddf[td_col] = ddf[td_col] - ddf[td_col].iloc[0]

                tu_col = udf.columns[0]
                if pd.api.types.is_numeric_dtype(udf[tu_col]):
                    udf[tu_col] = udf[tu_col] - udf[tu_col].iloc[0]

                tu = udf.columns[0]
                nums_u = udf.select_dtypes(include='number').columns.tolist()
                load_cols = [c for c in nums_u if c != tu and ("load" in c.lower() or "force" in c.lower())]
                lc = load_cols[0] if load_cols else [c for c in nums_u if c != tu][0]
                
                td = ddf.columns[0]
                nums_d = ddf.select_dtypes(include='number').columns.tolist()
                strain_cols = [c for c in nums_d if c != td and any(k in c.lower() for k in ["strain", "ε"])]
                sx = strain_cols[0] if strain_cols else [c for c in nums_d if c != td][0]

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
                ys, ys_idx, _ = calculate_yield_strength(eps_use, sig_use)
                if ys:
                    ys_val = ys
                    ax.plot(eps_use[ys_idx] * 100.0, ys, 'o', color=color, markersize=6)

                self.datasets.append({
                    "label": label, 
                    "color": color, 
                    "eps": eps_use, 
                    "sig": sig_use, 
                    "uts": uts, 
                    "ys": ys_val
                })
            except Exception as e:
                print(f"Error: {e}")

        ax.set_xlabel("True Strain (%)")
        ax.set_ylabel("True Stress (MPa)")
        ax.legend(loc="upper left")
        
        self._ensure_side_panel(fig)
        self._render_info_panel(
            rows=[(d["label"], d["color"], None, d["uts"], d.get("ys")) for d in self.datasets]
        )

        self.canvas.draw()
        if self.datasets: 
            self._init_span_selector(ax)

    def _on_select(self, x_min, x_max):
        """SpanSelector 완료"""
        if not self.datasets or x_max <= x_min: 
            return

        eps_min = x_min / 100.0
        eps_max = x_max / 100.0

        self._clear_span()
        ax = self.canvas.figure.axes[0]
        self.span = ax.axvspan(x_min, x_max, color="#00BCD4", alpha=0.22)
        self.vlines = [
            ax.axvline(x_min, color="#00ACC1", lw=2),
            ax.axvline(x_max, color="#00ACC1", lw=2),
        ]

        rows = []
        for d in self.datasets:
            eps = d["eps"]
            sig = d["sig"]
            msk = (eps >= eps_min) & (eps <= eps_max)
            E_mpa = self._fit_slope(eps[msk], sig[msk])
            rows.append((d["label"], d["color"], E_mpa, d["uts"], d.get("ys")))

        self._render_info_panel(rows=rows)

    def _manual_fit(self):
        """수동 범위 피팅"""
        if not self.datasets:
            return
        
        x_min = float(self.start_box.value())
        x_max = float(self.end_box.value())
        
        if x_max <= x_min:
            QMessageBox.warning(self, "Error", "End must be > Start.")
            return

        self._clear_span()
        ax = self.canvas.figure.axes[0]
        self.span = ax.axvspan(x_min, x_max, color="#00BCD4", alpha=0.22)
        self.vlines = [
            ax.axvline(x_min, color="#00ACC1", lw=2),
            ax.axvline(x_max, color="#00ACC1", lw=2),
        ]

        eps_min = x_min / 100.0
        eps_max = x_max / 100.0
        
        rows = []
        for d in self.datasets:
            msk = (d["eps"] >= eps_min) & (d["eps"] <= eps_max)
            E_mpa = self._fit_slope(d["eps"][msk], d["sig"][msk])
            rows.append((d["label"], d["color"], E_mpa, d["uts"], d.get("ys")))
        
        self._render_info_panel(rows=rows)
        self.canvas.draw_idle()

    def save_graph(self):
        """그래프 저장"""
        tr = self.lang_manager.translate if self.lang_manager else lambda x: x
        
        if self.canvas.figure is None:
            return
        
        path, _ = QFileDialog.getSaveFileName(
            self, 
            tr("data.save_graph"),
            "multi_compare.png", 
            "PNG (*.png);;JPEG (*.jpg);;PDF (*.pdf)"
        )
        if not path:
            return
            
        try:
            self.canvas.figure.savefig(path, dpi=300, bbox_inches='tight')
            QMessageBox.information(
                self, 
                tr("msg.saved"),
                tr("msg.saved_desc").format(os.path.basename(path))
            )
        except Exception as e:
            QMessageBox.warning(
                self, 
                tr("msg.error"),
                tr("msg.save_failed").format(e)
            )

    def retranslate(self):
        """UI 텍스트 번역 업데이트"""
        if not self.lang_manager:
            return
        
        tr = self.lang_manager.translate
        
        # 그룹박스
        self.ctrl.setTitle(tr("data.multi_compare"))
        
        # 버튼
        self.btn_load_multi.setText(tr("data.load_multiple"))
        self.btn_add_single.setText(tr("data.add_pair"))
        self.btn_edit_label.setText(tr("data.edit_label"))
        self.btn_remove_pair.setText(tr("data.remove_pair"))
        self.btn_plot.setText(tr("data.generate_multi"))
        self.btn_save_img_multi.setText(tr("data.save_graph"))
        self.btn_manual_fit.setText(tr("data.fit_by_range"))
        
        # 라벨
        self.pair_list_label.setText(tr("data.pairs_label"))
        self.default_tol_label.setText(tr("data.default_tol"))
        self.per_curve_tol_label.setText(tr("data.per_curve_tol"))
        self.geometry_label.setText(tr("data.geometry"))
        self.fit_range_label.setText(tr("data.manual_fit"))
        
        # GeometryInput 재번역
        if hasattr(self, 'geom'):
            self.geom.retranslate()
        
        # Pair 리스트 재표시
        self._refresh_pair_list()