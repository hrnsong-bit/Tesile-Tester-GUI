from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
from interfaces import IDataReceiver
import csv
import logging
from config import monitor_cfg  # ===== 추가 =====

logger = logging.getLogger(__name__)


class PlotService(IDataReceiver):
    """그래프 및 CSV 로깅"""
    
    def __init__(
        self, 
        main_window: QtWidgets.QMainWindow, 
        plot_widget: pg.PlotWidget, 
        ui=None, 
        temp_plot_widget: pg.PlotWidget = None
    ):
        if not plot_widget:
            logger.error("PlotWidget이 None입니다.")
            raise ValueError("plot_widget은 필수 인자입니다.")
            
        self.main_window = main_window
        self.plot_widget = plot_widget
        self.ui = ui
        self.temp_plot_widget = temp_plot_widget

        # 기본 테스트 플롯 초기화
        try:
            self.plot_item = self.plot_widget.getPlotItem()
            if not self.plot_item:
                raise ValueError("PlotItem을 가져올 수 없습니다.")
            
            self.data_line = self.plot_item.plot(pen='b')
        except Exception as e:
            logger.error(f"PlotItem 초기화 실패: {e}")
            raise
        
        # 데이터 저장소
        self.x_data = []
        self.y_data = []
        
        # ===== 추가: 최대 포인트 수 (config에서 로드) =====
        self.max_plot_points = monitor_cfg.MAX_PLOT_POINTS
        
        # 시간 측정기
        self.start_time = QtCore.QElapsedTimer()
        
        # 로그 파일
        self.log_file = None
        self.csv_writer = None
        
        # 플래그
        self._is_plotting = False

        # ===== 온도 플롯 관련 속성 =====
        self.temp_x = []
        self.temp_y = [[], [], [], []]
        self.temp_curves = []  # 통합 뷰용
        self.temp_curves_split = []  # 분할 뷰용 (4개)
        self._temp_initialized = False
        self.channel_visible = [True, True, True, True]
        
        # ===== 추가: 뷰 모드 =====
        self.temp_view_mode = 'unified'  # 'unified' or 'split'
        
        self._setup_plot()
        logger.info("PlotService 초기화 완료")
    
    def _setup_plot(self):
        """기본 테스트 그래프 설정"""
        try:
            self.plot_item.setLabel('bottom', 'Time', units='s')
            self.plot_item.setLabel('left', 'Load', units='N')
            self.plot_item.showGrid(x=True, y=True)
            self.plot_widget.setBackground('w')
        except Exception as e:
            logger.error(f"플롯 설정 실패: {e}")
    
    # ========================================================================
    # IDataReceiver 인터페이스 구현
    # ========================================================================
    
    def receive_motor_data(self, elapsed: float, displacement_um: float):
        """모터 데이터 수신"""
        pass
    
    def receive_loadcell_data(
        self, 
        force_n: float, 
        position_um: float, 
        temp_ch1: float
    ):
        """로드셀 데이터 수신"""
        if not self._is_plotting:
            return
        
        try:
            elapsed_sec = self.start_time.elapsed() / 1000.0
            
            # ===== 개선: 메모리 누수 방지 =====
            if len(self.x_data) >= self.max_plot_points:
                self.x_data.pop(0)
                self.y_data.pop(0)
            
            self.x_data.append(elapsed_sec)
            self.y_data.append(float(force_n))
            self.data_line.setData(self.x_data, self.y_data)
            
            if self.csv_writer:
                if temp_ch1 is not None:
                    self.csv_writer.writerow([
                        f"{elapsed_sec:.3f}",
                        f"{position_um:.3f}",
                        f"{force_n:.3f}",
                        f"{temp_ch1:.2f}"
                    ])
                else:
                    self.csv_writer.writerow([
                        f"{elapsed_sec:.3f}",
                        f"{position_um:.3f}",
                        f"{force_n:.3f}",
                        "N/A"
                    ])
        
        except Exception as e:
            logger.error(f"로드셀 데이터 처리 실패: {e}", exc_info=True)
    
    def receive_temp_data(self, elapsed: float, temps: list):
        """온도 데이터 수신"""
        if not self._temp_initialized:
            self.init_temp_plot()
            if not self._temp_initialized:
                return
        
        try:
            # ===== 개선: 메모리 누수 방지 =====
            if len(self.temp_x) >= self.max_plot_points:
                self.temp_x.pop(0)
                for i in range(4):
                    if len(self.temp_y[i]) > 0:
                        self.temp_y[i].pop(0)
            
            self.temp_x.append(elapsed)
            
            for i in range(min(len(temps), 4)):
                val = temps[i] if temps[i] is not None else 0.0
                self.temp_y[i].append(val)
            
            # ===== 수정: 뷰 모드에 따라 분기 =====
            if self.temp_view_mode == 'unified':
                self._update_unified_view()
            else:  # 'split'
                self._update_split_view()
            
            self._update_temp_xrange(elapsed)
        
        except Exception as e:
            logger.error(f"온도 데이터 처리 실패: {e}", exc_info=True)
    
    # ========================================================================
    # 플로팅 제어
    # ========================================================================
    
    def start_plotting(self) -> bool:
        """플로팅 및 로깅 시작"""
        if self._is_plotting:
            logger.warning("이미 플로팅이 진행 중입니다.")
            return False
        
        options = QtWidgets.QFileDialog.Options()
        filePath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.main_window, 
            "로그 파일 저장", 
            "",
            "CSV Files (*.csv);;All Files (*)", 
            options=options
        )

        if not filePath:
            logger.info("파일 저장을 취소했습니다.")
            return False

        try:
            self.log_file = open(filePath, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.log_file)
            self.csv_writer.writerow([
                'Time (s)', 
                'Position (um)', 
                'Load (N)',
                'Temp_CH1 (°C)'
            ])
            logger.info(f"로그 파일 생성: {filePath}")
            
        except PermissionError:
            logger.error(f"파일 접근 권한 없음: {filePath}")
            return False
        except Exception as e:
            logger.error(f"로그 파일 열기 실패: {e}")
            if self.log_file:
                try:
                    self.log_file.close()
                except:
                    pass
            self.log_file = None
            self.csv_writer = None
            raise

        self.x_data.clear()
        self.y_data.clear()
        self.data_line.setData(self.x_data, self.y_data)
        
        self.start_time.start()
        self._is_plotting = True
        
        return True

    def stop_plotting(self):
        """플로팅 및 로깅 중지"""
        if not self._is_plotting:
            return
            
        self._is_plotting = False

        if self.log_file:
            try:
                self.log_file.flush()
                self.log_file.close()
                logger.info("로그 파일 저장 완료")
            except Exception as e:
                logger.error(f"로그 파일 닫기 실패: {e}")
            finally:
                self.log_file = None
                self.csv_writer = None
    
    def clear_plot(self):
        """그래프 초기화"""
        try:
            self.x_data.clear()
            self.y_data.clear()
            self.data_line.setData(self.x_data, self.y_data)
        except Exception as e:
            logger.error(f"그래프 초기화 실패: {e}")
    
    # ========================================================================
    # 온도 플롯 관련 메서드
    # ========================================================================
    
    def set_temp_view_mode(self, mode: str):
        """
        온도 그래프 뷰 모드 설정
        
        Args:
            mode: 'unified' 또는 'split'
        """
        if mode not in ['unified', 'split']:
            logger.error(f"잘못된 뷰 모드: {mode}")
            return
        
        self.temp_view_mode = mode
        logger.info(f"온도 그래프 뷰 모드 변경: {mode}")
        
        # 기존 데이터로 즉시 갱신
        if self.temp_x:
            if mode == 'unified':
                self._update_unified_view()
            else:
                self._update_split_view()
    
    def init_temp_plot(self):
        """온도 그래프 초기화"""
        if self._temp_initialized:
            logger.debug("온도 플롯이 이미 초기화되었습니다.")
            return
        
        temp_widget = self.temp_plot_widget
        if not temp_widget and self.ui and hasattr(self.ui, 'temp_plot_unified'):
            temp_widget = self.ui.temp_plot_unified
        
        if not temp_widget:
            logger.warning("온도 플롯 위젯을 찾을 수 없습니다.")
            return

        try:
            colors = ['#EA002C', '#00A0E9', '#9BCF0A', '#F47725']
            
            # ===== 통합 뷰 초기화 =====
            temp_widget.addLegend(offset=(10, 10))
            
            self.temp_curves = []
            for i in range(4):
                pen = pg.mkPen(color=colors[i], width=2.5)
                curve = temp_widget.plot(
                    pen=pen, 
                    name=f"CH{i+1}", 
                    antialias=True
                )
                self.temp_curves.append(curve)
            
            plot_item = temp_widget.getPlotItem()
            if plot_item:
                plot_item.setLabel('bottom', 'Time', units='s')
                plot_item.setLabel('left', 'Temperature', units='°C')
                plot_item.showGrid(x=True, y=True, alpha=0.3)
            
            temp_widget.setBackground('w')
            
            # ===== 분할 뷰 초기화 =====
            if hasattr(self.ui, 'temp_plot_splits'):
                self.temp_curves_split = []
                for i, plot_widget in enumerate(self.ui.temp_plot_splits):
                    pen = pg.mkPen(color=colors[i], width=2.5)
                    curve = plot_widget.plot(pen=pen, antialias=True)
                    self.temp_curves_split.append(curve)
                    
                    plot_item = plot_widget.getPlotItem()
                    if plot_item:
                        plot_item.showGrid(x=True, y=True, alpha=0.3)
                    
                    plot_widget.setBackground('w')
            
            self._connect_checkboxes()
            self._connect_view_mode_buttons()
            self._temp_initialized = True
            
            logger.info("온도 플롯 초기화 완료 (통합/분할 모두)")
            
        except Exception as e:
            logger.error(f"온도 플롯 초기화 실패: {e}", exc_info=True)
    
    def _update_unified_view(self):
        """통합 뷰 업데이트 (4채널 한 화면)"""
        for i in range(4):
            if i < len(self.temp_curves) and self.temp_curves[i]:
                if self.channel_visible[i]:
                    self.temp_curves[i].setData(
                        self.temp_x, 
                        self.temp_y[i],
                        connect='finite'
                    )
                else:
                    self.temp_curves[i].setData([], [])
    
    def _update_split_view(self):
        """분할 뷰 업데이트 (4개 그래프)"""
        if not hasattr(self, 'temp_curves_split') or not self.temp_curves_split:
            return
        
        for i in range(4):
            if i < len(self.temp_curves_split) and self.temp_curves_split[i]:
                if self.channel_visible[i]:
                    self.temp_curves_split[i].setData(
                        self.temp_x, 
                        self.temp_y[i],
                        connect='finite'
                    )
                else:
                    self.temp_curves_split[i].setData([], [])
    
    def update_temp_plot(self, elapsed: float, temps: list):
        """온도 데이터를 실시간 그래프에 업데이트"""
        if not self._temp_initialized:
            logger.warning("온도 플롯이 초기화되지 않았습니다. 초기화를 시도합니다.")
            self.init_temp_plot()
            if not self._temp_initialized:
                return
        
        self.receive_temp_data(elapsed, temps)
    
    def _connect_checkboxes(self):
        """체크박스 연결"""
        if not self.ui or not hasattr(self.ui, 'temp_channels'):
            return
        
        try:
            for i in range(1, 5):
                if i in self.ui.temp_channels:
                    chk = self.ui.temp_channels[i]['chk']
                    try:
                        chk.stateChanged.disconnect()
                    except TypeError:
                        pass
                    chk.stateChanged.connect(
                        lambda state, ch=i-1: self._on_channel_toggled(ch, state)
                    )
        except Exception as e:
            logger.error(f"체크박스 연결 실패: {e}")
    
    def _connect_view_mode_buttons(self):
        """뷰 모드 버튼 연결"""
        if not self.ui:
            return
        
        try:
            if hasattr(self.ui, 'temp_view_unified'):
                self.ui.temp_view_unified.toggled.connect(
                    lambda checked: self._on_view_mode_changed('unified') if checked else None
                )
            
            if hasattr(self.ui, 'temp_view_split'):
                self.ui.temp_view_split.toggled.connect(
                    lambda checked: self._on_view_mode_changed('split') if checked else None
                )
            
            logger.info("뷰 모드 버튼 연결 완료")
        except Exception as e:
            logger.error(f"뷰 모드 버튼 연결 실패: {e}")
    
    def _on_view_mode_changed(self, mode: str):
        """뷰 모드 변경 콜백"""
        self.set_temp_view_mode(mode)
        
        # 스택 위젯 전환
        if hasattr(self.ui, 'temp_plot_stack'):
            if mode == 'unified':
                self.ui.temp_plot_stack.setCurrentIndex(0)
            else:
                self.ui.temp_plot_stack.setCurrentIndex(1)
    
    def _on_channel_toggled(self, channel_index: int, state: int):
        """체크박스 토글 콜백"""
        try:
            is_checked = (state == QtCore.Qt.Checked)
            self.channel_visible[channel_index] = is_checked
            
            # 즉시 갱신
            if self.temp_view_mode == 'unified':
                if channel_index < len(self.temp_curves):
                    if is_checked and len(self.temp_x) > 0:
                        self.temp_curves[channel_index].setData(
                            self.temp_x, 
                            self.temp_y[channel_index]
                        )
                    else:
                        self.temp_curves[channel_index].setData([], [])
            else:  # split
                if channel_index < len(self.temp_curves_split):
                    if is_checked and len(self.temp_x) > 0:
                        self.temp_curves_split[channel_index].setData(
                            self.temp_x, 
                            self.temp_y[channel_index]
                        )
                    else:
                        self.temp_curves_split[channel_index].setData([], [])
        except Exception as e:
            logger.error(f"채널 토글 실패: {e}")
    
    def _update_temp_xrange(self, current_time: float):
        """X축 범위를 최근 60초로 제한"""
        if self.temp_view_mode == 'unified':
            temp_widget = self.temp_plot_widget
            if not temp_widget and self.ui:
                temp_widget = getattr(self.ui, 'temp_plot_unified', None)
            
            if temp_widget and len(self.temp_x) > 0:
                plot_item = temp_widget.getPlotItem()
                if plot_item:
                    if current_time > 60:
                        plot_item.setXRange(current_time - 60, current_time, padding=0)
                    else:
                        plot_item.setXRange(0, max(60, current_time), padding=0)
        else:  # split
            if hasattr(self.ui, 'temp_plot_splits'):
                for plot_widget in self.ui.temp_plot_splits:
                    if len(self.temp_x) > 0:
                        plot_item = plot_widget.getPlotItem()
                        if plot_item:
                            if current_time > 60:
                                plot_item.setXRange(current_time - 60, current_time, padding=0)
                            else:
                                plot_item.setXRange(0, max(60, current_time), padding=0)
    
    def clear_temp_plot(self):
        """온도 그래프 초기화"""
        if not self._temp_initialized:
            return
        
        try:
            self.temp_x.clear()
            for i in range(4):
                self.temp_y[i].clear()
            
            # 통합 뷰 초기화
            for i in range(len(self.temp_curves)):
                self.temp_curves[i].setData([], [])
            
            # 분할 뷰 초기화
            if hasattr(self, 'temp_curves_split'):
                for i in range(len(self.temp_curves_split)):
                    self.temp_curves_split[i].setData([], [])
            
            logger.info("온도 그래프 초기화 완료")
        except Exception as e:
            logger.error(f"온도 그래프 초기화 실패: {e}")
