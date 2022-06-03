import asyncio
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

from websocket_server import WebSocketServer
from websocket_client import WebSocketClient



logger = logging.getLogger(__name__)

def terminate_safely(python_process, timeout=3):
    python_process.join(timeout)
    if(python_process.is_alive()):
        #python_process.terminate() #sends SIGTERM signal
        os.kill(python_process.pid, signal.SIGKILL) #sends SIGKILL signal
        python_process.join() #should always exit


def main():
    mongo_client = Client()
    mongo_client.videtics.datasets.drop()
    datasets = [{'dataset':'dataset1' , 'folders':'folder3', 'user' : 'anass'} , {'dataset':'dataset2' , 'folders':'folder3', 'user' : 'anass'} , {'dataset':'dataset3' , 'folders':'folder1', 'user' : 'anass'}]
    mongo_client.videtics.datasets.insert_many(datasets)
    
    datasets = mongo_client.videtics.datasets.find({"folders" : "folder3" })
    for t in datasets:
        t['_id'] = str(t['_id'])
        self.send_response(t)
        self.logger.warning(t["dataset"])
    #os.system('python3 resize_kitti.py --parent_dir /workspace/dataset/test25 --dest_dir /workspace/dataset1/  --resize 960,544 --keep_aspect_ratio')

    
    
    i = 0
    
    while True:
        
        
        if self.stop_event.is_set():
            self.logger.warning('DvcServer: Stop required by main process')
            break
        
        try:
            self.logger.warning('im waiting...')            
            cmd = self.command_message_queue.get_nowait()
        except queue.Empty:                
            pass 
        else:

            self.logger.warning("######################BEGINING RESIZING##########################")
            self.logger.warning(cmd)
            export_dir = cmd['export_directory'].split('/')[-1]
            datasets = mongo_client.videtics.datasets.find({"folders" : export_dir })
            for d in datasets:
                d['_id'] = str(d['_id'])
                os.system('python3 resize_kitti.py --parent_dir ' +cmd['export_directory']+ ' --dest_dir /workspace/'+str(d["dataset"])+'/'+' --resize 960,544 --keep_aspect_ratio')
                self.logger.warning(d["dataset"])
            #python3 resize_kitti.py --parent_dir /raid/dataset/detection_dataset/VDSDataset/thermal --dest_dir /raid/dataset/dataset_for_tao/detection/thermal/inverted_included/960-544  --resize 960,544 --keep_aspect_ratio

            self.logger.warning("######################END RESIZING##########################")
        time.sleep(.100)



"""mongo_client.videtics.users.drop()
            response = [{'command' : "Rodger that", 'user' : cmd['user']}]
            mongo_client.videtics.users.insert_many(response)
            
            self.logger.warning('hello there')
            
            rs = mongo_client.videtics.users.find({})
            self.logger.warning("#####################BEGINING###########################")
            i = 0 
            for t in rs:
                self.logger.warning(i)
                t['_id'] = str(t['_id'])
                self.send_response(t)
            self.logger.warning("######################END##########################")
    
while True:
        

        try:

            local_ip_adress = "0.0.0.0"
            local_port = 4000

            stop_event = Event()
            socket_command_message_queue = Queue()
            socket_message_queue = Queue()


            websocket_server = WebSocketServer(stop_event, socket_message_queue, socket_command_message_queue, local_ip_adress, local_port)
            websocket_server.start()


            while not stop_event.is_set():

                try: 
                    
                    logger.error("in the main loop")

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
    main()"""