import asyncio
import websockets
import sys
import os
import traceback
import multiprocessing
import datetime
import time
import json
import queue
import math
import logging
from multiprocessing import Queue, Event
from websocket_client import WebSocketClient
from websocket_server import WebSocketServer
from dvc_server import DvcServer

logger = logging.getLogger(__name__)

def terminate_safely(python_process, timeout=3):
    python_process.join(timeout)
    if(python_process.is_alive()):
        #python_process.terminate() #sends SIGTERM signal
        os.kill(python_process.pid, signal.SIGKILL) #sends SIGKILL signal
        python_process.join() #should always exit


def main():
    while True:

        try:


            stop_event = Event()
            socket_command_message_queue = Queue()
            socket_message_queue = Queue()

            dvc_command_queue = Queue()
            dvc_message_queue = Queue()

            websocket_client = WebSocketClient("192.168.110.46", 5000, socket_message_queue, socket_command_message_queue)
            websocket_client.set_access_route("192.168.110.46", 5000, "dvcserver")
            websocket_client.start()

            dvc_server = DvcServer(stop_event, socket_command_message_queue, dvc_command_queue)
            dvc_server.start()


            while not stop_event.is_set():

                try:   
                    cmd = socket_message_queue.get_nowait()
                    if 'commandType' in cmd :
                        if cmd['commandType'] == "createFolder" or cmd['commandType'] == "createDataset" or cmd['commandType'] == "DvcExport" or cmd['commandType'] == "folderList":
                            logger.warning("i'm in dvc2")
                            dvc_command_queue.put(cmd)


                except queue.Empty:
                    pass

                time.sleep(.100)



        except: #Exception as e:
            logger.error("Exception in main process: ")
            logger.error(traceback.format_exc())

        finally:
            logger.warning("Stopping all processes ...")
            if not stop_event.is_set():                
                stop_event.set()

            
            logger.info("Disposing websocket server ...")
            if websocket_server is not None:
                terminate_safely(websocket_server)
            logger.info("-> websocket server disposed.")

            logger.warning("All process terminated")

        #sleep x seconds whene reloading after global watchdog issue
        time.sleep(5)


if __name__ == '__main__':
    main()