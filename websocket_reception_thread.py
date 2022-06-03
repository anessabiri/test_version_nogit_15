from multiprocessing import Queue, Event
import queue
import time

from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QThreadPool
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QMessageBox, QWidget, QDialog, QHBoxLayout


class WebsocketReceptionThread(QThread):
    connection_refused_signal = pyqtSignal()
    connection_accepted_signal = pyqtSignal(list)

    project_list_received_signal = pyqtSignal(list)
    user_list_received_signal = pyqtSignal(list)
    file_list_received_signal = pyqtSignal(dict)
    export_state_update_received_signal = pyqtSignal(dict)
    logs_search_received_signal = pyqtSignal(dict)
    

    def __init__(self, websocket_rcv_msg_queue):
        QThread.__init__(self)
        self.is_client_running = True
        self.websocket_rcv_msg_queue = websocket_rcv_msg_queue  

    def run(self):
        while self.is_client_running:
            try:
                msg = self.websocket_rcv_msg_queue.get_nowait()
            except queue.Empty:
                pass
            else:
                # print(str.format("Queue size {}", self.websocket_rcv_msg_queue.qsize()))
                if "firstAuthResponse" in msg:
                    if msg["taskList"] is None:
                        self.connection_refused_signal.emit()
                    else:
                        self.connection_accepted_signal.emit(msg["taskList"])
                
                elif "projectList" in msg:
                    print(msg["projectList"])
                    self.project_list_received_signal.emit(msg["projectList"])
                
                elif "userList" in msg:
                    self.user_list_received_signal.emit(msg["userList"])
                elif "fileList" in msg:
                    self.file_list_received_signal.emit(msg)
                elif "ExportStateUpdate" in msg:
                    self.export_state_update_received_signal.emit(msg["ExportStateUpdate"])
                elif "logsExist" in msg:
                    self.logs_search_received_signal.emit(msg)



                    
            time.sleep(0.010)