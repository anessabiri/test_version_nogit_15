import multiprocessing as mp
import traceback
import logging
import random
import queue
import time
import json
import copy
import sys
import os
from os import path, system

from queue import Queue, Empty

import numpy as np
import toolbox as tlbx
import threading

from cli.cli import nested_command


class CvatRelayQueryServer(mp.Process):

    def __init__(self, stop_event, event_message_queue, command_message_queue):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.stop_event = stop_event
        self.event_message_queue = event_message_queue
        self.command_message_queue = command_message_queue

    
    def send_response(self, event):
        self.event_message_queue.put(event)
    
    
    def run(self):

        while True:

            if self.stop_event.is_set():
                self.logger.warning('CvatRelayServer: Stop required by main process')
                break
            
            try:                
                cmd = self.command_message_queue.get_nowait()
            except Empty:                
                pass 
            else:
                if "firstAuth" in cmd:
                    task_list = nested_command(cmd["commandDict"])
                    response = {"firstAuthResponse" : True, "taskList" : task_list, "user" : cmd["user"]}
                    self.send_response(response)
                elif cmd["commandType"] == "projectList":
                    project_list = nested_command(cmd["commandDict"])
                    response = {"projectList" : project_list, "user" : cmd["user"]}
                    self.send_response(response)
                elif cmd["commandType"] == "userList":
                    user_list = nested_command(cmd["commandDict"])
                    response = {"userList" : user_list, "user" : cmd["user"]}
                    self.send_response(response)
                elif "patch" in cmd["commandType"]:
                    nested_command(cmd["commandDict"])
                elif cmd["commandType"] == "taskInfo":
                    task_info = nested_command(cmd["commandDict"])
                    response = {"taskInfo" : task_info, "user" : cmd["user"]}
                    self.send_response(response)
                elif cmd["commandType"] == "taskThumbnail":
                    task_thumbnail = nested_command(cmd["commandDict"])
                    response = {"taskThumbnail" : task_thumbnail, "user" : cmd["user"]}
                    self.send_response(response)
            
            time.sleep(.100)

