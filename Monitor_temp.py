# Monitor_temp.py
import time
import logging
from PyQt5 import QtCore
from pymodbus.client.serial import ModbusSerialClient

logger = logging.getLogger(__name__)

class TempWorker(QtCore.QObject):
    temp_ready = QtCore.pyqtSignal(list)

    def __init__(self, client: ModbusSerialClient, interval_ms: int):
        super().__init__()
        self.client = client
        self.interval_ms = interval_ms
        self._running = False
        self.addr_list = [0x03E8, 0x03EE, 0x03F4, 0x03FA]

    @QtCore.pyqtSlot()
    def run(self):
        self._running = True
        while self._running:
            start_time = time.time()
            if self.client and self.client.is_socket_open():
                current_temps = []
                try:
                    for addr in self.addr_list:
                        res = self.client.read_input_registers(address=addr, count=1)
                        if not res.isError():
                            val = res.registers[0]
                            current_temps.append(val)  # 1도 단위 그대로
                        else:
                            current_temps.append(None)
                    self.temp_ready.emit(current_temps)
                except Exception as e:
                    logger.error(f"Temp Monitor Error: {e}")
            
            elapsed = (time.time() - start_time) * 1000
            time.sleep(max(0, (self.interval_ms - elapsed) / 1000.0))

    def stop(self):
        self._running = False

class TempMonitor(QtCore.QObject):
    def __init__(self, client, update_callback, interval_ms=500):
        super().__init__()
        self.thread = QtCore.QThread()
        self.worker = TempWorker(client, interval_ms)
        self.worker.moveToThread(self.thread)
        self.worker.temp_ready.connect(update_callback)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

    def stop(self):
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()