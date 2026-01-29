# Plot_Service.py
import csv
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
import logging

logger = logging.getLogger(__name__)

class PlotService:
    def __init__(self, main_window: QtWidgets.QMainWindow, plot_widget: pg.PlotWidget, ui=None, temp_plot_widget: pg.PlotWidget = None):
        """
        PlotService 초기화
        
        Args:
            main_window: 파일 대화상자의 부모 윈도우
            plot_widget: 기본 테스트용 그래프 위젯
            ui: GUI 객체 참조 (온도 플롯 접근용)
            temp_plot_widget: 온도 전용 그래프 위젯 (옵션)
        """
        if not plot_widget:
            logger.error("PlotWidget이 None입니다.")
            raise ValueError("plot_widget은 필수 인자입니다.")
            
        self.main_window = main_window
        self.plot_widget = plot_widget
        self.ui = ui
        self.temp_plot_widget = temp_plot_widget

        # ===== 기본 테스트 플롯 초기화 =====
        try:
            self.plot_item = self.plot_widget.getPlotItem()
            if not self.plot_item:
                raise ValueError("PlotItem을 가져올 수 없습니다.")
            
            self.data_line = self.plot_item.plot(pen='b')
        except Exception as e:
            logger.error(f"PlotItem 초기화 실패: {e}")
            raise
        
        # 데이터 저장소 (그래프용)
        self.x_data = []
        self.y_data = []
        
        # 시간 측정기
        self.start_time = QtCore.QElapsedTimer()
        
        # 로그 파일 핸들러
        self.log_file = None
        self.csv_writer = None
        
        # 플래그
        self._is_plotting = False

        # 기본 플롯 설정
        self._setup_plot()
        
        # ===== 온도 플롯 초기화 =====
        self.temp_x = []
        self.temp_y = [[], [], [], []]
        self.temp_curves = []
        self._temp_initialized = False
        
        # 채널별 표시 상태 (기본값: 모두 표시)
        self.channel_visible = [True, True, True, True]
        
        logger.info("PlotService 초기화 완료")

    def _setup_plot(self):
        """기본 테스트 그래프의 속성을 설정합니다."""
        try:
            self.plot_item.setLabel('bottom', 'Time', units='s')
            self.plot_item.setLabel('left', 'Load', units='N')
            self.plot_item.showGrid(x=True, y=True)
            self.plot_widget.setBackground('w')
            logger.debug("기본 플롯 설정 완료")
        except Exception as e:
            logger.error(f"플롯 설정 실패: {e}")

    # ==================== 기본 테스트 플롯 메서드 ====================
    
    def start_plotting(self) -> bool:
        """
        플로팅 및 로깅을 시작합니다.
        """
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
            self.csv_writer.writerow(['Time (s)', 'Position (um)', 'Load (N)'])
            logger.info(f"로그 파일 생성: {filePath}")
            
        except PermissionError:
            logger.error(f"파일 접근 권한 없음: {filePath}")
            QtWidgets.QMessageBox.warning(
                self.main_window,
                "파일 오류",
                f"파일에 접근할 수 없습니다:\n{filePath}"
            )
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

        logger.info("플로팅 시작 (데이터 초기화)")
        self.x_data.clear()
        self.y_data.clear()
        self.data_line.setData(self.x_data, self.y_data)
        
        self.start_time.start()
        self._is_plotting = True
        
        return True

    def stop_plotting(self):
        """플로팅 및 로깅을 중지합니다."""
        if not self._is_plotting:
            logger.debug("이미 플로팅이 중지된 상태입니다.")
            return
            
        logger.info("플로팅 및 로깅 중지")
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

    def update_data(self, load_n: float, pos_um: float):
        """
        새로운 데이터를 받아 그래프를 업데이트하고 CSV에 기록합니다.
        """
        if not self._is_plotting:
            return

        try:
            elapsed_sec = self.start_time.elapsed() / 1000.0
            
            self.x_data.append(elapsed_sec)
            self.y_data.append(float(load_n))
            
            self.data_line.setData(self.x_data, self.y_data)
            
            if self.csv_writer:
                self.csv_writer.writerow([
                    f"{elapsed_sec:.3f}",
                    f"{pos_um:.3f}",
                    f"{load_n:.3f}"
                ])
            
        except Exception as e:
            logger.error(f"update_data 예외: {e}", exc_info=True)
            self._is_plotting = False

    def clear_plot(self):
        """그래프 데이터를 초기화합니다."""
        try:
            self.x_data.clear()
            self.y_data.clear()
            self.data_line.setData(self.x_data, self.y_data)
            logger.debug("그래프 데이터 초기화 완료")
        except Exception as e:
            logger.error(f"그래프 초기화 실패: {e}")

    # ==================== 온도 플롯 메서드 ====================
    
    def init_temp_plot(self):
        """
        온도 그래프를 초기화합니다.
        """
        if self._temp_initialized:
            logger.debug("온도 플롯이 이미 초기화되었습니다.")
            return
        
        temp_widget = self.temp_plot_widget
        if not temp_widget and self.ui and hasattr(self.ui, 'temp_plot'):
            temp_widget = self.ui.temp_plot
        
        if not temp_widget:
            logger.warning("온도 플롯 위젯을 찾을 수 없습니다.")
            return

        try:
            # 채널별 색상
            colors = [
                '#EA002C',  # SK Red (CH1)
                '#00A0E9',  # SK Blue (CH2)
                '#9BCF0A',  # SK Green (CH3)
                '#F47725'   # SK Orange (CH4)
            ]
            
            # 범례 추가
            temp_widget.addLegend(offset=(10, 10))
            
            # 4개 채널에 대한 커브 생성
            self.temp_curves = []
            for i in range(4):
                pen = pg.mkPen(
                    color=colors[i], 
                    width=2.5,
                    style=QtCore.Qt.SolidLine
                )
                
                curve = temp_widget.plot(
                    pen=pen,
                    name=f"CH{i+1}",
                    antialias=True,
                    clipToView=True,
                    autoDownsample=True
                )
                self.temp_curves.append(curve)
            
            # 축 설정
            plot_item = temp_widget.getPlotItem()
            if plot_item:
                plot_item.setLabel('bottom', 'Time', units='s', **{'font-size': '12pt'})
                plot_item.setLabel('left', 'Temperature', units='°C', **{'font-size': '12pt'})
                
                plot_item.showGrid(x=True, y=True, alpha=0.3)
                
                # X축 범위 제한 (0 이하로 가지 않도록)
                plot_item.setLimits(xMin=0)
                
                # 초기 X축 범위 설정 (0 ~ 60초)
                plot_item.setXRange(0, 60, padding=0)
                
                # Y축 자동 조정
                plot_item.enableAutoRange(axis='y', enable=True)
                
                # 마우스 상호작용
                plot_item.setMouseEnabled(x=True, y=True)
                plot_item.showButtons()
                
                # ViewBox 제한
                view_box = plot_item.getViewBox()
                if view_box:
                    view_box.setLimits(xMin=0, xMax=None, yMin=None, yMax=None)
            
            # 배경 흰색
            temp_widget.setBackground('w')
            
            # 성능 최적화
            temp_widget.setClipToView(True)
            temp_widget.setDownsampling(auto=True, mode='peak')
            
            # ===== 체크박스 연결 =====
            self._connect_checkboxes()
            
            self._temp_initialized = True
            logger.info("온도 플롯 초기화 완료 (체크박스 연동)")
            
        except Exception as e:
            logger.error(f"온도 플롯 초기화 실패: {e}", exc_info=True)

    def _connect_checkboxes(self):
        """
        UI의 체크박스를 그래프 표시/숨김 기능에 연결합니다.
        """
        if not self.ui or not hasattr(self.ui, 'temp_channels'):
            logger.warning("UI 또는 temp_channels를 찾을 수 없습니다.")
            return
        
        try:
            for i in range(1, 5):
                if i in self.ui.temp_channels:
                    chk = self.ui.temp_channels[i]['chk']
                    
                    # 기존 연결 해제 (중복 방지)
                    try:
                        chk.stateChanged.disconnect()
                    except:
                        pass
                    
                    # 람다 함수로 채널 번호 전달
                    chk.stateChanged.connect(
                        lambda state, channel=i-1: self._on_channel_toggled(channel, state)
                    )
                    
                    logger.debug(f"CH{i} 체크박스 연결 완료")
            
            logger.info("모든 체크박스 연결 완료")
            
        except Exception as e:
            logger.error(f"체크박스 연결 실패: {e}", exc_info=True)

    def _on_channel_toggled(self, channel_index: int, state: int):
        """
        체크박스 상태 변경 시 호출되는 콜백
        
        Args:
            channel_index: 채널 인덱스 (0~3)
            state: Qt.Checked(2) 또는 Qt.Unchecked(0)
        """
        try:
            is_checked = (state == QtCore.Qt.Checked)
            self.channel_visible[channel_index] = is_checked
            
            # 해당 채널의 커브 표시/숨김
            if channel_index < len(self.temp_curves) and self.temp_curves[channel_index]:
                if is_checked:
                    # 데이터가 있으면 다시 표시
                    if len(self.temp_x) > 0:
                        self.temp_curves[channel_index].setData(
                            self.temp_x, 
                            self.temp_y[channel_index]
                        )
                    logger.info(f"CH{channel_index+1} 그래프 표시")
                else:
                    # 데이터를 빈 리스트로 설정하여 숨김
                    self.temp_curves[channel_index].setData([], [])
                    logger.info(f"CH{channel_index+1} 그래프 숨김")
            
        except Exception as e:
            logger.error(f"채널 토글 실패 (CH{channel_index+1}): {e}", exc_info=True)

    def update_temp_plot(self, elapsed: float, temps: list):
        """
        온도 데이터를 그래프에 업데이트합니다.
        """
        if not self._temp_initialized:
            logger.warning("온도 플롯이 초기화되지 않았습니다.")
            self.init_temp_plot()
            if not self._temp_initialized:
                return
        
        try:
            # 시간이 음수가 되지 않도록 보호
            elapsed = max(0.0, elapsed)
            
            self.temp_x.append(elapsed)
            
            # 각 채널의 온도 데이터 추가
            for i in range(min(len(temps), 4)):
                val = temps[i] if temps[i] is not None else 0.0
                temp_celsius = val
                self.temp_y[i].append(temp_celsius)
                
                # ===== 체크박스가 켜진 채널만 업데이트 =====
                if i < len(self.temp_curves) and self.temp_curves[i]:
                    if self.channel_visible[i] and len(self.temp_x) > 1:
                        self.temp_curves[i].setData(
                            self.temp_x, 
                            self.temp_y[i],
                            connect='finite'
                        )
                    elif not self.channel_visible[i]:
                        # 체크박스가 꺼진 채널은 빈 데이터 유지
                        self.temp_curves[i].setData([], [])
            
            # X축 자동 스크롤 (최근 60초만 표시)
            temp_widget = self.temp_plot_widget
            if not temp_widget and self.ui and hasattr(self.ui, 'temp_plot'):
                temp_widget = self.ui.temp_plot
            
            if temp_widget and len(self.temp_x) > 0:
                plot_item = temp_widget.getPlotItem()
                if plot_item:
                    current_time = self.temp_x[-1]
                    
                    if current_time > 60:
                        plot_item.setXRange(
                            current_time - 60,
                            current_time,
                            padding=0
                        )
                    else:
                        plot_item.setXRange(0, max(60, current_time), padding=0)
            
            # 메모리 관리 (1000개 초과 시 삭제)
            max_points = 1000
            if len(self.temp_x) > max_points:
                if self.temp_x[0] > 0:
                    self.temp_x.pop(0)
                    for i in range(4):
                        if len(self.temp_y[i]) > 0:
                            self.temp_y[i].pop(0)
                        
        except Exception as e:
            logger.error(f"온도 플롯 업데이트 실패: {e}", exc_info=True)

    def clear_temp_plot(self):
        """온도 그래프 데이터를 초기화합니다."""
        if not self._temp_initialized:
            return
        
        try:
            self.temp_x.clear()
            for i in range(4):
                self.temp_y[i].clear()
                if i < len(self.temp_curves) and self.temp_curves[i]:
                    self.temp_curves[i].setData([], [])
            
            # X축 범위를 0으로 리셋
            temp_widget = self.temp_plot_widget
            if not temp_widget and self.ui and hasattr(self.ui, 'temp_plot'):
                temp_widget = self.ui.temp_plot
            
            if temp_widget:
                plot_item = temp_widget.getPlotItem()
                if plot_item:
                    plot_item.setXRange(0, 60, padding=0)
            
            logger.debug("온도 그래프 데이터 초기화 완료")
        except Exception as e:
            logger.error(f"온도 그래프 초기화 실패: {e}")

    # ==================== 리소스 정리 ====================
    
    def cleanup(self):
        """모든 리소스를 안전하게 정리합니다."""
        logger.info("PlotService 리소스 정리 시작")
        
        if self._is_plotting:
            self.stop_plotting()
        
        if self.log_file:
            try:
                self.log_file.close()
            except:
                pass
            finally:
                self.log_file = None
                self.csv_writer = None
        
        self.x_data.clear()
        self.y_data.clear()
        self.temp_x.clear()
        for channel in self.temp_y:
            channel.clear()
        
        logger.info("PlotService 리소스 정리 완료")

    def __del__(self):
        """소멸자: 객체 삭제 시 자동으로 리소스 정리"""
        try:
            self.cleanup()
        except:
            pass