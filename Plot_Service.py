# Plot_Service.py
import csv
from PyQt5 import QtCore, QtWidgets
import pyqtgraph as pg
import logging

# 해당 파일 전용 로거 생성
logger = logging.getLogger(__name__)

class PlotService:
    def __init__(self, main_window: QtWidgets.QMainWindow, plot_widget: pg.PlotWidget):
        if not plot_widget:
            logger.error("PlotWidget이 None입니다.")
            return
            
        self.main_window = main_window # 파일 대화상자 부모
        self.plot_widget = plot_widget

        # 1. 정의 (Define First)
        # plot_widget에서 실제 PlotItem 객체를 가져와 self.plot_item에 할당합니다.
        self.plot_item = self.plot_widget.getPlotItem() 

        # 2. 사용 (Use Second)
        # self.plot_item이 정의된 후에 plot() 메서드를 호출합니다.
        self.data_line = self.plot_item.plot(pen='b') 
        
        # 데이터 저장소 (그래프용)
        self.x_data = [] # 시간 (s)
        self.y_data = [] # 하중 (N)
        
        # 시간 측정기
        self.start_time = QtCore.QElapsedTimer()
        
        # 로그 파일 핸들러
        self.log_file = None
        self.csv_writer = None
        
        # 플래그
        self._is_plotting = False

        # 3. 정의 후에 호출 (Call after definition)
        # self.plot_item이 완전히 정의된 후에 _setup_plot을 호출합니다.
        self._setup_plot() 
        
        # 3. print -> logger.info
        logger.info("초기화 완료")

    def _setup_plot(self):
        """그래프의 기본 속성(레이블, 그리드)을 설정합니다."""
        # 이 함수는 self.plot_item이 존재한다고 가정하고 호출됩니다.
        self.plot_item.setLabel('bottom', 'Time', units='s')
        self.plot_item.setLabel('left', 'Load', units='N')
        self.plot_item.showGrid(x=True, y=True)
        self.plot_widget.setBackground('w') # 배경 흰색

    def start_plotting(self) -> bool: # [!!] 성공/실패(취소) 여부 반환
        """
        플로팅 및 로깅을 시작합니다.
        CSV 저장 경로를 묻고, 실패 시 False를 반환합니다.
        """
        
        # 1. 파일 저장 대화상자 열기
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filePath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.main_window, 
            "로그 파일 저장", 
            "", # 기본 경로
            "CSV Files (*.csv);;All Files (*)", 
            options=options
        )

        # 2. 사용자가 취소한 경우
        if not filePath:
            logger.info("파일 저장을 취소했습니다. 시작하지 않습니다.")
            return False

        # 3. 파일 열기 및 CSV writer 준비
        try:
            # newline=''은 CSV 파일에 빈 줄이 생기는 것을 방지합니다.
            self.log_file = open(filePath, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.log_file)
            
            # 헤더(제목) 작성
            self.csv_writer.writerow(['Time (s)', 'Position (um)', 'Load (N)'])
            logger.info(f"로그 파일 생성: {filePath}")
            
        except Exception as e:
            logger.error(f"로그 파일을 여는 데 실패했습니다: {e}")
            self.log_file = None
            self.csv_writer = None
            # (오류 메시지는 Main.py의 QMessageBox가 대신 보여줄 것입니다)
            raise e # 오류를 Main.py로 다시 전달

        # 4. (기존 로직) 그래프 데이터 초기화
        logger.info("Start Plotting (데이터 초기화)")
        self.x_data.clear()
        self.y_data.clear()
        self.data_line.setData(self.x_data, self.y_data) 
        
        # 5. 시간 및 플래그 설정
        self.start_time.start()
        self._is_plotting = True
        return True # [!!] 성공

    def stop_plotting(self):
        """플로팅 및 로깅을 중지합니다."""
        if not self._is_plotting:
            return
            
        logger.info("Stop Plotting & Logging")
        self._is_plotting = False

        # 파일 닫기
        try:
            if self.log_file:
                self.log_file.close()
                logger.info("로그 파일 저장 완료.")
        except Exception as e:
            logger.error(f"로그 파일 닫기 실패: {e}")
        
        self.log_file = None
        self.csv_writer = None

    def update_data(self, load_n: float, pos_um: float):
        """
        새로운 데이터를 받아 그래프를 업데이트하고 CSV에 기록합니다.
        """
        if not self._is_plotting:
            return

        try:
            # 1. 경과 시간 계산 (초 단위)
            elapsed_sec = self.start_time.elapsed() / 1000.0
            
            # 2. 그래프 데이터 추가 (하중 vs 시간)
            self.x_data.append(elapsed_sec)
            self.y_data.append(float(load_n))
            
            # 3. 그래프 업데이트
            self.data_line.setData(self.x_data, self.y_data)
            
            # 4. CSV 파일에 기록 (시간, 위치, 하중)
            if self.csv_writer:
                self.csv_writer.writerow([
                    f"{elapsed_sec:.3f}",  # 시간 (소수점 3자리)
                    f"{pos_um:.3f}",       # 위치 (소수점 3자리)
                    f"{load_n:.3f}"        # 하중 (소수점 3자리)
                ])
            
        except Exception as e:
            logger.error(f"update_data 예외: {e}")
            self._is_plotting = False # 오류 발생 시 중지