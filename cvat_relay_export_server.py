import multiprocessing as mp
import traceback
import logging
import random
import queue
import time
import json
import copy
import sys
import csv
import os
from os import path, system

from queue import Queue, Empty

import numpy as np
import toolbox as tlbx
import threading
import xml.etree.ElementTree as ET

from xml_reader import XMLReaderForKitti, XMLReaderForIdTracking, XMLReaderForComposedAttributes, XMLReaderForSimpleAttribute
from cli.cli import nested_command
from exception_wrapper import ExceptionWrapper

from transforms.cvat_to_coco import add_xml_to_data, to_json_coco

class CvatRelayExportServer(mp.Process):

    def __init__(self, stop_event, event_message_queue, command_message_queue, exception_message_queue):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.stop_event = stop_event
        self.event_message_queue = event_message_queue
        self.command_message_queue = command_message_queue
        self.exception_message_queue = exception_message_queue

        self.process_kitti_tasks_queue = mp.Queue()
        self.process_kitti_tasks_thread = threading.Thread(target=self.process_kitti_tasks_thread_run, daemon=True)
        self.process_kitti_tasks_thread.start()

        self.process_id_tracking_tasks_queue = mp.Queue()
        self.process_id_tracking_tasks_thread = threading.Thread(target=self.process_id_tracking_tasks_thread_run, daemon=True)
        self.process_id_tracking_tasks_thread.start()

        self.process_pose_coco_tasks_queue = mp.Queue()
        self.process_pose_coco_tasks_thread = threading.Thread(target=self.process_pose_coco_tasks_thread_run, daemon=True)
        self.process_pose_coco_tasks_thread.start()

        self.process_composed_attributes_tasks_queue = mp.Queue()
        self.process_composed_attributes_tasks_thread = threading.Thread(target=self.process_composed_attributes_tasks_thread_run, daemon=True)
        self.process_composed_attributes_tasks_thread.start()

        self.process_simple_attribute_tasks_queue = mp.Queue()
        self.process_simple_attribute_tasks_thread = threading.Thread(target=self.process_simple_attribute_tasks_thread_run, daemon=True)
        self.process_simple_attribute_tasks_thread.start()

        if not path.exists("/workspace/downloads/"):
            system("mkdir /workspace/downloads")
        else:
            system("rm -rf /workspace/downloads/*")

    
    def send_response(self, event):
        self.event_message_queue.put(event)
    
    def send_exception(self, exception):
        self.exception_message_queue.put({"exception" : exception})
    
    @staticmethod
    def remove_task(json_object, task_name):
        invalid_frames_id = [int(image["id"]) for image in json_object["images"] if image["file_name"].split("_")[0] == task_name]
        if len(invalid_frames_id) == 0:
            return
        min_id, n_invalids = min(invalid_frames_id),len(invalid_frames_id)

        new_images = []
        for image in json_object["images"]:
            if not image["id"] in invalid_frames_id:
                image['id'] = get_new_id(n_invalids,min_id,image['id'])
                new_images.append(image)
        new_annotations = []
        for k, annt in enumerate(json_object["annotations"]):
            if not annt["image_id"] in invalid_frames_id:
                annt['image_id'] = get_new_id(n_invalids,min_id,annt['image_id'])
                annt['id'] = k
                new_annotations.append(annt)
        
        json_object["images"] = new_images
        json_object["annotations"] = new_annotations
        
    @staticmethod
    def merge_jsons_coco(json_1, json_2):
        n_images_1, n_annots_1 = len(json_1["images"]), len(json_1["annotations"])
        for image in json_2["images"]:
            image["id"] += n_images_1
        for annt in json_2["annotations"]:
            annt["image_id"] += n_images_1
            annt["id"] += n_annots_1
        json_1["images"] += json_2["images"]
        json_1["annotations"] += json_2["annotations"]
    
    def process_pose_coco_tasks_thread_run(self):
        try:
            while True:
                try:
                    element = self.process_pose_coco_tasks_queue.get_nowait()
                except Empty:
                    time.sleep(.20)
                else:
                    export_arg_list, user = element
                    command_dict, export_dir_path, task_to_process_list, total_operation_nb, option, logs_dict, override_option = export_arg_list
                    
                    images, coco_annotations, action_annotations = [], [], []
    
                    for task_idx, task_dict in enumerate(task_to_process_list):
                        command_dict['filename'] = '/workspace/downloads/' + task_dict["task_name"].replace(' ', '_') + '_' + command_dict['fileformat'].replace(' ', '_') +  '.zip'
                        command_dict['task_id'] = task_dict["task_id"]
                        result = nested_command(command_dict)
                        self.send_response({"ExportStateUpdate" : {"category" : "download", "label" : "Téléchargements : " + str(task_idx+1) + "/" + str(len(task_to_process_list)), "progress" : (task_idx+1)*100/total_operation_nb}, "user" : user})
                    
                    for task_idx, task_dict in enumerate(task_to_process_list):
                        self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : 0}, "user" : user})
                        system("unzip /workspace/downloads/" + str(task_dict["task_name"].replace(' ', '_')) + "_" + command_dict['fileformat'].replace(' ', '_') + '.zip' + " -d /workspace/downloads/" + str(task_dict["task_name"].replace(' ', '_')) + "_" + command_dict['fileformat'].replace(' ', '_'))
                        
                        cvat_video_img_dir_path = path.join("/workspace/downloads/" + task_dict["task_name"].replace(' ', '_') + "_CVAT_for_video_1.1", "images/")
                        img_file_list = tlbx.get_directory_img_files(cvat_video_img_dir_path)            
                        cvat_video_xml_path = path.join("/workspace/downloads/" + task_dict["task_name"].replace(' ', '_') + "_CVAT_for_video_1.1", "annotations.xml")

                        if not os.path.exists(path.join(export_dir_path, "images/")):
                            os.system("mkdir " + path.join(export_dir_path, "images"))
                        for img_path in img_file_list:
                            os.system('cp ' + (img_path.replace(' ', '\ ')) + ' ' + (path.join(export_dir_path, "images/"+ task_dict["task_name"].replace(' ', '_') + '_' + path.splitext(path.basename(img_path))[0] + '.PNG').replace(' ', '\ ')))

                        self.logger.warning("Loading xml task...")
                        
                        add_xml_to_data(images, coco_annotations, action_annotations, cvat_video_xml_path)

                        self.logger.warning("xml task added...")
                        
                        logs_dict["task_done"][task_dict["task_id"]] = task_dict["task_name"]
                        with open(export_dir_path + '/logs.json','w') as fp:
                            json.dump(logs_dict, fp)
                        
                        # if self.logs_state :
                        #     self.log_export(task_dict)
                        self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : 100}, "user" : user})
                        self.send_response({"ExportStateUpdate" : {"category" : "global_export", "label" : "Exports : " + str(task_idx+1) + "/" + str(len(task_to_process_list)), "progress" : 50 + (task_idx+1)*100/total_operation_nb}, "user" : user})
                        system('rm -rf /workspace/downloads/' + str(task_dict["task_name"].replace(' ', '_')) + '*')
                    
                    self.logger.warning("coco annotations to json...")
                    json_tasks_coco = to_json_coco(images, coco_annotations)
                    self.logger.warning("action annotations to json...")
                    json_tasks_actions = to_json_coco(images, action_annotations)
    
                    #if override_option == 'keep_existing':
                    #    with open(export_dir_path + '/annotations.json', 'r') as f:
                    #        existing_json_tasks = json.load(f)
                    #    CvatRelayExportServer.merge_jsons_coco(json_tasks, existing_json_tasks)

                    with open(export_dir_path + '/annotations.json', "w") as outfile: 
                        json.dump(json_tasks_coco, outfile, indent=None)
                    with open(export_dir_path + '/annotations_actions.json', "w") as outfile: 
                        json.dump(json_tasks_actions, outfile, indent=None)
                    
                    self.send_response({"ExportStateUpdate" : {"category" : "hide"}, "user" : user})
        except Exception as e:
            self.send_exception(ExceptionWrapper(e))


    def process_kitti_tasks_thread_run(self):
        try:
            while True:
                try:
                    element = self.process_kitti_tasks_queue.get_nowait()
                except Empty:
                    time.sleep(.20)
                else:
                    export_arg_list, user = element
                    command_dict_list, export_dir_path, task_to_process_list, total_operation_nb, option, logs_dict = export_arg_list
                    for task_idx, task_dict in enumerate(task_to_process_list):
                        for command_dict in command_dict_list:
                            command_dict['filename'] = '/workspace/downloads/' + task_dict["task_name"].replace(' ', '_') + '_' + command_dict['fileformat'].replace(' ', '_') +  '.zip'
                            command_dict['task_id'] = task_dict["task_id"]
                            self.logger.warning("Launching task data download ...")
                            result = nested_command(command_dict)
                            self.logger.warning("Download completed ...")
                        self.send_response({"ExportStateUpdate" : {"category" : "download", "label" : "Téléchargements : " + str(task_idx+1) + "/" + str(len(task_to_process_list)), "progress" : (task_idx+1)*100/total_operation_nb}, "user" : user})
                    
                    for task_idx, task_dict in enumerate(task_to_process_list):
                        self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : 0}, "user" : user})
                        for command_dict in command_dict_list:
                            system("unzip /workspace/downloads/" + str(task_dict["task_name"].replace(' ', '_')) + "_" + command_dict['fileformat'].replace(' ', '_') + '.zip' + " -d /workspace/downloads/" + str(task_dict["task_name"].replace(' ', '_')) + "_" + command_dict['fileformat'].replace(' ', '_'))
                        
                        label_img_img_dir_path = path.join("/workspace/downloads/" + task_dict["task_name"].replace(' ', '_') + "_ImageNet_1.0", "no_label/")
                        for file in os.listdir(label_img_img_dir_path):
                            os.system("mv " + label_img_img_dir_path.replace(' ', '_') + str(file) + " " + label_img_img_dir_path.replace(' ', '_') + str(file)[9:])
                        img_file_list = tlbx.get_directory_img_files(label_img_img_dir_path)            
                        pascal_voc_xml_dir_path = path.join("/workspace/downloads/" + task_dict["task_name"].replace(' ', '_') + "_PASCAL_VOC_1.1", "Annotations/")

                        for idx, img_file in  enumerate(img_file_list):
                            img_name = img_file.split('/')[-1][:-4]
                            if not path.exists(pascal_voc_xml_dir_path + img_name + '.xml'):
                                system("touch " + pascal_voc_xml_dir_path.replace(' ', '_') + img_name + '.xml')

                        xml_file_list = tlbx.get_directory_xml_files(pascal_voc_xml_dir_path)
                        for idx, xml_file in enumerate(xml_file_list):
                            img_file = label_img_img_dir_path + path.splitext(path.basename(xml_file))[0] + '.PNG'
                            xml_reader = XMLReaderForKitti(xml_file, img_file, task_dict["task_name"].replace(' ', '_'), export_dir_path)
                            xml_reader.export_kitti(option)
                            self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : idx*100/len(xml_file_list)}, "user" : user})
                            self.send_response({"ExportStateUpdate" : {"category" : "global_export", "progress" : 50 + (task_idx+(idx/len(xml_file_list)))*100/total_operation_nb}, "user" : user})
                        logs_dict["task_done"][task_dict["task_id"]] = task_dict["task_name"]
                        with open(export_dir_path + '/logs.json','w') as fp:
                            json.dump(logs_dict, fp)
                        
                        # if self.logs_state :
                        #     self.log_export(task_dict)
                        self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : 100}, "user" : user})
                        self.send_response({"ExportStateUpdate" : {"category" : "global_export", "label" : "Exports : " + str(task_idx+1) + "/" + str(len(task_to_process_list)), "progress" : 50 + (task_idx+1)*100/total_operation_nb}, "user" : user})
                        system('rm -rf /workspace/downloads/' + str(task_dict["task_name"].replace(' ', '_')) + '*')
                    
                    self.send_response({"ExportStateUpdate" : {"category" : "hide"}, "user" : user})
        except Exception as e:
            self.send_exception(ExceptionWrapper(e))
    
    def process_id_tracking_tasks_thread_run(self):
        try:
            while True:
                try:
                    element = self.process_id_tracking_tasks_queue.get_nowait()
                except Empty:
                    time.sleep(.20)
                else:
                    export_arg_list, user = element
                    command_dict_list, export_dir_path, task_to_process_list, total_operation_nb, option, logs_dict = export_arg_list
                    for task_idx, task_dict in enumerate(task_to_process_list):
                        for command_dict in command_dict_list:
                            command_dict['filename'] = '/workspace/downloads/' + task_dict["task_name"].replace(' ', '_') + '_' + command_dict['fileformat'].replace(' ', '_') +  '.zip'
                            command_dict['task_id'] = task_dict["task_id"]
                            self.logger.warning("Launching task data download ...")
                            result = nested_command(command_dict)
                            self.logger.warning("Download completed ...")
                        self.send_response({"ExportStateUpdate" : {"category" : "download", "label" : "Téléchargements : " + str(task_idx+1) + "/" + str(len(task_to_process_list)), "progress" : (task_idx+1)*100/total_operation_nb}, "user" : user})
                    
                    for task_idx, task_dict in enumerate(task_to_process_list):
                        self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : 0}, "user" : user})
                        for command_dict in command_dict_list:
                            system("unzip /workspace/downloads/" + str(task_dict["task_name"].replace(' ', '_')) + "_" + command_dict['fileformat'].replace(' ', '_') + '.zip' + " -d /workspace/downloads/" + str(task_dict["task_name"].replace(' ', '_')) + "_" + command_dict['fileformat'].replace(' ', '_'))
                        
                        label_img_img_dir_path = path.join("/workspace/downloads/" + task_dict["task_name"].replace(' ', '_') + "_ImageNet_1.0", "no_label/")
                        for file in os.listdir(label_img_img_dir_path):
                            os.system("mv " + label_img_img_dir_path.replace(' ', '_') + str(file) + " " + label_img_img_dir_path.replace(' ', '_') + str(file)[9:])
                        img_file_list = tlbx.get_directory_img_files(label_img_img_dir_path)            
                        pascal_voc_xml_dir_path = path.join("/workspace/downloads/" + task_dict["task_name"].replace(' ', '_') + "_PASCAL_VOC_1.1", "Annotations/")

                        xml_file_list = tlbx.get_directory_xml_files(pascal_voc_xml_dir_path)
                        for idx, xml_file in enumerate(xml_file_list):
                            img_file = label_img_img_dir_path + path.splitext(path.basename(xml_file))[0] + '.PNG'
                            xml_reader = XMLReaderForIdTracking(xml_file, img_file, task_dict["task_name"].replace(' ', '_'), export_dir_path)
                            xml_reader.export_id_tracking(option)
                            self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : idx*100/len(xml_file_list)}, "user" : user})
                            self.send_response({"ExportStateUpdate" : {"category" : "global_export", "progress" : 50 + (task_idx+(idx/len(xml_file_list)))*100/total_operation_nb}, "user" : user})
                        logs_dict["task_done"][task_dict["task_id"]] = task_dict["task_name"]
                        with open(export_dir_path + '/logs.json','w') as fp:
                            json.dump(logs_dict, fp)
                        
                        # if self.logs_state :
                        #     self.log_export(task_dict)
                        self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : 100}, "user" : user})
                        self.send_response({"ExportStateUpdate" : {"category" : "global_export", "label" : "Exports : " + str(task_idx+1) + "/" + str(len(task_to_process_list)), "progress" : 50 + (task_idx+1)*100/total_operation_nb}, "user" : user})
                        system('rm -rf /workspace/downloads/' + str(task_dict["task_name"].replace(' ', '_')) + '*')
                    
                    self.send_response({"ExportStateUpdate" : {"category" : "hide"}, "user" : user})
        except Exception as e:
            self.send_exception(ExceptionWrapper(e))
    
    def process_composed_attributes_tasks_thread_run(self):
        try:
            while True:
                try:
                    element = self.process_composed_attributes_tasks_queue.get_nowait()
                except Empty:
                    time.sleep(.20)
                else:
                    export_arg_list, user = element
                    command_dict_list, export_dir_path, task_to_process_list, total_operation_nb, option, logs_dict = export_arg_list
                    reduced_csv_columns = ['fname', 'gender', 'hair', 'upper_body_color', 'lower_body_color', 'sleeves_up', 'down_length', 'clothes', 'hat', 'backpack', 'bag']
                    int_columns = ['gender', 'hair', 'sleeves_up', 'down_length', 'clothes', 'hat', 'backpack', 'bag']
                    int_translation = [('male', 'female'), ('short', 'long'), ('short', 'long'), ('short', 'long'), ('trousers', 'skirt'), ('no', 'yes'), ('no', 'yes'), ('no', 'yes'), ('no', 'yes')]
                    csv_path = path.join(export_dir_path, "apr_annotation.csv")
                    csv_open = open(csv_path, 'w')
                    csv_writer = csv.DictWriter(csv_open, fieldnames=reduced_csv_columns, extrasaction='ignore')
                    csv_writer.writeheader()
                    for task_idx, task_dict in enumerate(task_to_process_list):
                        for command_dict in command_dict_list:
                            command_dict['filename'] = '/workspace/downloads/' + task_dict["task_name"].replace(' ', '_') + '_' + command_dict['fileformat'].replace(' ', '_') +  '.zip'
                            command_dict['task_id'] = task_dict["task_id"]
                            self.logger.warning("Launching task data download ...")
                            result = nested_command(command_dict)
                            self.logger.warning("Download completed ...")
                        self.send_response({"ExportStateUpdate" : {"category" : "download", "label" : "Téléchargements : " + str(task_idx+1) + "/" + str(len(task_to_process_list)), "progress" : (task_idx+1)*100/total_operation_nb}, "user" : user})
                    
                    for task_idx, task_dict in enumerate(task_to_process_list):
                        self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : 0}, "user" : user})
                        for command_dict in command_dict_list:
                            system("unzip /workspace/downloads/" + str(task_dict["task_name"].replace(' ', '_')) + "_" + command_dict['fileformat'].replace(' ', '_') + '.zip' + " -d /workspace/downloads/" + str(task_dict["task_name"].replace(' ', '_')) + "_" + command_dict['fileformat'].replace(' ', '_'))
                        
                        label_img_img_dir_path = path.join("/workspace/downloads/" + task_dict["task_name"].replace(' ', '_') + "_ImageNet_1.0", "no_label/")
                        for file in os.listdir(label_img_img_dir_path):
                            os.system("mv " + label_img_img_dir_path.replace(' ', '_') + str(file) + " " + label_img_img_dir_path.replace(' ', '_') + str(file)[9:])
                        img_file_list = tlbx.get_directory_img_files(label_img_img_dir_path)            
                        pascal_voc_xml_dir_path = path.join("/workspace/downloads/" + task_dict["task_name"].replace(' ', '_') + "_PASCAL_VOC_1.1", "Annotations/")

                        xml_file_list = tlbx.get_directory_xml_files(pascal_voc_xml_dir_path)
                        for idx, xml_file in enumerate(xml_file_list):
                            img_file = label_img_img_dir_path + path.splitext(path.basename(xml_file))[0] + '.PNG'
                            xml_reader = XMLReaderForComposedAttributes(xml_file, img_file, task_dict["task_name"].replace(' ', '_'), export_dir_path, csv_writer)
                            xml_reader.export_composed_attributes(option)
                            self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : idx*100/len(xml_file_list)}, "user" : user})
                            self.send_response({"ExportStateUpdate" : {"category" : "global_export", "progress" : 50 + (task_idx+(idx/len(xml_file_list)))*100/total_operation_nb}, "user" : user})
                        logs_dict["task_done"][task_dict["task_id"]] = task_dict["task_name"]
                        with open(export_dir_path + '/logs.json','w') as fp:
                            json.dump(logs_dict, fp)
                        
                        # if self.logs_state :
                        #     self.log_export(task_dict)
                        self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : 100}, "user" : user})
                        self.send_response({"ExportStateUpdate" : {"category" : "global_export", "label" : "Exports : " + str(task_idx+1) + "/" + str(len(task_to_process_list)), "progress" : 50 + (task_idx+1)*100/total_operation_nb}, "user" : user})
                        system('rm -rf /workspace/downloads/' + str(task_dict["task_name"].replace(' ', '_')) + '*')
                    
                    self.send_response({"ExportStateUpdate" : {"category" : "hide"}, "user" : user})
        except Exception as e:
            self.send_exception(ExceptionWrapper(e))
    

    def process_simple_attribute_tasks_thread_run(self):
        try:
            while True:
                try:
                    element = self.process_simple_attribute_tasks_queue.get_nowait()
                except Empty:
                    time.sleep(.20)
                else:
                    export_arg_list, user = element
                    command_dict_list, export_dir_path, task_to_process_list, total_operation_nb, option, logs_dict = export_arg_list
                    for task_idx, task_dict in enumerate(task_to_process_list):
                        for command_dict in command_dict_list:
                            command_dict['filename'] = '/workspace/downloads/' + task_dict["task_name"].replace(' ', '_') + '_' + command_dict['fileformat'].replace(' ', '_') +  '.zip'
                            command_dict['task_id'] = task_dict["task_id"]
                            self.logger.warning("Launching task data download ...")
                            result = nested_command(command_dict)
                            self.logger.warning("Download completed ...")
                        self.send_response({"ExportStateUpdate" : {"category" : "download", "label" : "Téléchargements : " + str(task_idx+1) + "/" + str(len(task_to_process_list)), "progress" : (task_idx+1)*100/total_operation_nb}, "user" : user})
                    
                    for task_idx, task_dict in enumerate(task_to_process_list):
                        self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : 0}, "user" : user})
                        for command_dict in command_dict_list:
                            system("unzip /workspace/downloads/" + str(task_dict["task_name"].replace(' ', '_')) + "_" + command_dict['fileformat'].replace(' ', '_') + '.zip' + " -d /workspace/downloads/" + str(task_dict["task_name"].replace(' ', '_')) + "_" + command_dict['fileformat'].replace(' ', '_'))
                        
                        label_img_img_dir_path = path.join("/workspace/downloads/" + task_dict["task_name"].replace(' ', '_') + "_ImageNet_1.0", "no_label/")
                        for file in os.listdir(label_img_img_dir_path):
                            os.system("mv " + label_img_img_dir_path.replace(' ', '_') + str(file) + " " + label_img_img_dir_path.replace(' ', '_') + str(file)[9:])
                        img_file_list = tlbx.get_directory_img_files(label_img_img_dir_path)            
                        pascal_voc_xml_dir_path = path.join("/workspace/downloads/" + task_dict["task_name"].replace(' ', '_') + "_PASCAL_VOC_1.1", "Annotations/")

                        xml_file_list = tlbx.get_directory_xml_files(pascal_voc_xml_dir_path)
                        for idx, xml_file in enumerate(xml_file_list):
                            img_file = label_img_img_dir_path + path.splitext(path.basename(xml_file))[0] + '.PNG'
                            xml_reader = XMLReaderForSimpleAttribute(xml_file, img_file, task_dict["task_name"].replace(' ', '_'), export_dir_path)
                            xml_reader.export_simple_attribute(option)
                            self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : idx*100/len(xml_file_list)}, "user" : user})
                            self.send_response({"ExportStateUpdate" : {"category" : "global_export", "progress" : 50 + (task_idx+(idx/len(xml_file_list)))*100/total_operation_nb}, "user" : user})
                        logs_dict["task_done"][task_dict["task_id"]] = task_dict["task_name"]
                        with open(export_dir_path + '/logs.json','w') as fp:
                            json.dump(logs_dict, fp)
                        
                        # if self.logs_state :
                        #     self.log_export(task_dict)
                        self.send_response({"ExportStateUpdate" : {"category" : "export", "progress" : 100}, "user" : user})
                        self.send_response({"ExportStateUpdate" : {"category" : "global_export", "label" : "Exports : " + str(task_idx+1) + "/" + str(len(task_to_process_list)), "progress" : 50 + (task_idx+1)*100/total_operation_nb}, "user" : user})
                        system('rm -rf /workspace/downloads/' + str(task_dict["task_name"].replace(' ', '_')) + '*')
                    
                    self.send_response({"ExportStateUpdate" : {"category" : "hide"}, "user" : user})
        except Exception as e:
            self.send_exception(ExceptionWrapper(e))

    def run(self):
        try:
            while True:

                if self.stop_event.is_set():
                    self.logger.warning('CvatRelayExportServer: Stop required by main process')
                    break
                
                try:                
                    cmd = self.command_message_queue.get_nowait()
                except Empty:                
                    pass 
                else:
                    if cmd["commandType"] == "exportDetectionKitti":
                        self.process_kitti_tasks_queue.put([cmd["exportArgList"], cmd["user"]])
                    if cmd["commandType"] == "exportDetectionToId":
                        self.process_id_tracking_tasks_queue.put([cmd["exportArgList"], cmd["user"]])
                    elif cmd["commandType"] == "exportPoseCoco":
                        self.process_pose_coco_tasks_queue.put([cmd["exportArgList"], cmd["user"]])
                    elif cmd["commandType"] == "exportComposedAttributes":
                        self.process_composed_attributes_tasks_queue.put([cmd["exportArgList"], cmd["user"]])
                    elif cmd["commandType"] == "exportSimpleAttribute":
                        self.process_simple_attribute_tasks_queue.put([cmd["exportArgList"], cmd["user"]])
                    elif cmd["commandType"] == "deleteExport":
                        system("rm -rf " + cmd["exportDirPath"] + "/*")
                    elif cmd["commandType"] == "searchLogs":
                        if not path.exists(cmd["exportDirPath"] + '/logs.json'):
                            self.send_response({"logsExist" : False, "user" : cmd["user"]})
                        else:
                            with open(cmd["exportDirPath"] + '/logs.json', 'r') as f:
                                logs_dict = json.load(f)
                            self.send_response({"logsExist" : True, "logsDict" : logs_dict, "user" : cmd["user"]})
                
                time.sleep(.100)
        except Exception as e:
            self.send_exception(ExceptionWrapper(e))

