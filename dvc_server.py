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
from queue import Queue
from mongo_client import Client
import os
import subprocess


class DvcServer(mp.Process):

    def __init__(self, stop_event, event_message_queue, command_message_queue):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.stop_event = stop_event
        self.event_message_queue = event_message_queue
        self.command_message_queue = command_message_queue
    

    def send_response(self, event):
        self.event_message_queue.put(event)
    
    def update_version(self, current_version, update_type): 
        version = current_version.split('.')
        if int(version[2]) == 9 : 
            version[2] = 0
            if int(version[1]) == 9:
              version[1] = 0
              version[0] = int(version[0]) + 1  
            else :
              version[1] = int(version[1]) + 1 
        else : 
            version[2] = int(version[2]) + 1 
        return str(version[0]) + '.' +str(version[1]) + '.' + str(version[2])
        
    
    def run(self):

        mongo_client = Client()
        
        """os.makedirs("/raid/dataset/dataset_for_tao2/test_version_nogit_19")
                                
                                os.chdir("/raid/dataset/dataset_for_tao2/test_version_nogit_19")
                                self.logger.warning("Directory Created ... ")
                                os.system('curl -u anessabiri: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 https://api.github.com/user/repos -d \'{"name":"test_version_nogit_19"}\'')
                                self.logger.warning('done in github')
                                os.system("git init")
                                os.system("echo \"readme\" >> README.md")
                                os.system("git add README.md")
                                os.system("git config --global user.email \"anessabiri3@gmail.com\" ")
                                os.system("git config --global user.name \"anessabiri\"")
                                os.system("git commit -m \"first commit\"")
                                os.system("git remote add origin https://anessabiri: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@github.com/anessabiri/test_version_nogit_19.git")
                                os.system("git branch -M main")
                                os.system("git push -u origin main")
                        
                                os.makedirs("/raid/dataset/dataset_for_tao2/test_version_nogit_19/all")
                                os.system("echo \"readme\" >> ./all/README2.md")
                                os.system("dvc init")
                                os.system("dvc remote add --default ssh-storage ssh://videtics@bp.videtics.net/raid/remote_storage2/data")
                                os.system("dvc remote modify ssh-storage port 32901")
                                os.system("dvc remote modify ssh-storage ask_password false")
                                os.system("dvc remote modify --local ssh-storage password v1d3t1cs4dgx@2021")
                                os.system("dvc add all")
                                os.system("git add all.dvc")
                                self.logger.warning("update the dataset")
                                #datasets_ = mongo_client.videtics.datasets.find_one({"dataset_name":"test_version2"})
                                os.system("git config --global user.email \"anessabiri3@gmail.com\" ")
                                os.system("git config --global user.name \"anessabiri\"")
                                os.system("git commit -m \"First commit  version \" ")
                                os.system("git tag -a \"0.0.7\" "+  "-m \"first tag\"")
                                os.system("git push --set-upstream origin main")
                                os.system("dvc config cache.shared group")"""
        os.system("chmod 777 -R /raid/dataset/dataset_for_tao2/test_version_nogit_19/")
        #os.system("pip install dvc[ssh]")
        #os.system("dvc push")
        self.logger.warning("Pulled")
        """os.system("git config --global user.email \"anessabiri3@gmail.com\" ")
                                os.system("git config --global user.name \"anessabiri\"")"""

        #os.system("git remote add origin https://anessabiri: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@github.com/anessabiri/test_version_nogit_8")
        #os.system("git branch -M main")


        """os.system("dvc add all")
                                os.system("git add --all")
                                os.system("chown $(whoami) ~/raid/dataset/dataset_for_tao2/test_version4")
                                os.system("git config --global user.email \"anessabiri3@gmail.com\" ")
                                os.system("git config --global user.name \"anessabiri\"")
                                os.system("git commit -m \"commit  version = 0.0.5\"")"""
        #mongo_client.videtics.datasets.drop()
        #datasets = [{'dataset_name':'dataset1' , 'folder_list':['folder2','folder13'],"current_version" : '0.0.0',"dataset_type" : "detection"} , {'dataset_name':'dataset2' , 'folder_list':['folder2'],"current_version" : '0.0.0',"dataset_type" : "detection"} , {'dataset_name':'dataset3' , 'folder_list':['folder1'],"current_version" : '0.0.0',"dataset_type" : "detection"}]
        #mongo_client.videtics.datasets.insert_many(datasets)
        """datasets_ = mongo_client.videtics.datasets.find({})
                                for t in datasets_:
                                    t['_id'] = str(t['_id'])
                                    #self.send_response(t)
                                    self.logger.warning(t)"""
               
        while True:            
            if self.stop_event.is_set():
                self.logger.warning('DvcServer: Stop required by main process')
                break
            
            try:    
                cmd = self.command_message_queue.get_nowait()
                self.logger.warning('i get it...') 
            except queue.Empty:               
                pass 

            else:
                if cmd['commandType'] == "folderList":
                    try:
                        datasets = mongo_client.videtics.datasets.find({})
                        all_folders_duplicates= []
                        all_floders_list = []
                        all_dataset_list = []
                        self.logger.warning('im listing folders...')
                        for data in datasets:
                            data['_id'] = str(data['_id'])
                            all_folders_duplicates +=data['folder_list']
                            all_dataset_list.append((data['dataset_name'],data['folder_list'],data["current_version"],data["dataset_type"]))
                        for i in all_folders_duplicates:
                            if i not in all_floders_list:
                                all_floders_list.append(i)
                        self.logger.warning(all_floders_list)
                        self.logger.warning("this the user")
                        self.logger.warning(cmd['client_user'])
                        self.send_response({"commandType" : "FolderListAnnotation" , "folderList" : all_floders_list , "datasetList" : all_dataset_list ,"client_user" : cmd['client_user']})

                    except :
                        self.logger.warning("Error in FolderListRequest ...")
                elif cmd['commandType'] == "createFolder":
                    self.logger.warning(cmd)
                    try:
                        new_dir = str(cmd['pathFolder'])+str(cmd['folderName'])
                        os.makedirs(new_dir)
                        for d in cmd['dataSets'] : 
                            datasets = mongo_client.videtics.datasets.find({"dataset_name" : str(d)})
                            for dataset in datasets :
                                mongo_client.videtics.datasets.update_one({"_id":dataset["_id"]},{"$set":{"folder_list":dataset['folder_list']+[cmd['folderName']]}})
                                #dataset['folder_list'] =  dataset['folder_list']+[cmd['folderName']]
                                self.logger.warning(dataset)
                        self.logger.warning("#######################################")
                        datasets = mongo_client.videtics.datasets.find({})
                        for data in datasets:
                            self.logger.warning(data)
                        self.send_response({"commandType" : "FolderIsAdded", "client_user" : cmd['client_user']})
                    except FileExistsError:
                        self.logger.warning("Directory already exists ...")
                elif cmd['commandType'] == "createDataset":
                    try:
                        # Create target Directory
                        new_dir = str(cmd['pathDataset'])+str(cmd['datasetName'])
                        os.makedirs(new_dir+'/all/tfrecords')
                        self.logger.warning("Directory Created ... ")
                        os.system("curl -u" +" anessabiri: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" + " https://api.github.com/user/repos -d " + '\'{"name":"'+str(cmd['datasetName'])+'"}\'')
                        self.logger.warning('done in github')
                        current_directory = os.getcwd()
                        os.chdir(new_dir)
                        os.system("git init")
                        os.system("echo \"readme\" >> README.md")
                        os.system("git add README.md")
                        os.system("git config --global user.email \"anessabiri3@gmail.com\" ")
                        os.system("git config --global user.name \"anessabiri\"")
                        os.system("git commit -m \"first commit\"")
                        os.system("git remote add origin https://anessabiri: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@github.com/anessabiri/"+str(cmd['datasetName'])+".git")
                        os.system("git branch -M main")
                        os.system("git push -u origin main")
                        os.chdir(current_directory)
                        dataset = [{'dataset_name': str(cmd['datasetName']),'dataset_type': str(cmd['dataset_type']), 'folder_list':cmd['folder_list'],"current_version" : '0.0.0' , 'latest_version' :'0.0.0' , 'version_list' : ['0.0.0'] , 'ip_adress' :'0.0.0.0','number_images_per_version' :[0],'classes_per_version':[0] }]
                        self.logger.warning(' all is good  in github...')
                        mongo_client.videtics.datasets.insert_many(dataset)
                        self.send_response({"commandType" : "DatasetIsAdded", "client_user" : cmd['client_user']})
                    except FileExistsError:
                        self.logger.warning("Directory already exists ...")
                    self.logger.warning('done all is good ...')

                elif cmd['commandType'] == "DvcExport":
                    if cmd["inversionAugmentation"] :
                        self.logger.warning("###################### AUGMENTATION ##########################")
                        os.system('python3 invert_thermal_script.py --src_img_dir ' +cmd['export_directory'])
                    self.logger.warning("######################BEGINING RESIZING##########################")
                    self.logger.warning(cmd)
                    export_dir = cmd['export_directory'].split('/')[-1]
                    datasets = mongo_client.videtics.datasets.find({"folder_list" : {"$in":[export_dir]}})

                    #/!\ajouter le directory des dataset ou le fixer
                    self.send_response({"commandType" : "BeginExport" , "current_user" :cmd['current_user']}) 

                    for d in datasets:
                        d['_id'] = str(d['_id'])
                        os.system('python3 resize_kitti.py --parent_dir ' +cmd['export_directory']+ ' --dest_dir /raid/dataset/dataset_for_tao2/'+str(d["dataset_name"])+'/all/'+' --resize 960,544 --keep_aspect_ratio')
                        directory = '/raid/dataset/dataset_for_tao2/'+str(d["dataset_name"])
                        current_directory = os.getcwd()
                        os.chdir(directory)
                        if d["current_version"] == '0.0.0' :
                            self.logger.warning('$$$$$$$$$$$$$$$$$$$$dvc initialisation ... $$$$$$$$$$$$$$$$$$$$$$$$$$$')
                            os.system("dvc init")
                            os.system("dvc remote add --default ssh-storage ssh://videtics@bp.videtics.net/raid/remote_storage2/data")
                            os.system("dvc remote modify ssh-storage port 32900")
                            #os.system("dvc remote modify ssh-storage ask_password false")
                            os.system("dvc remote modify --local ssh-storage password v1d3t1cs4dgx@2021")
                            os.system("dvc add all")
                            os.system("git add --all")
                            self.logger.warning('dvc initialisation done...')
                            new_version = self.update_version('0.0.0',cmd['version_type'])
                            dataset = { "dataset_name": d["dataset_name"] }
                            old_version_list = mongo_client.videtics.datasets.find_one({"dataset_name": d["dataset_name"]})["version_list"]
                            old_version_list.append(new_version)
                            newvalues = { "$set": { "current_version": new_version , "latest_version" : new_version , "version_list" : old_version_list } }
                            mongo_client.videtics.datasets.update_one(dataset, newvalues)
                            #self.logger.warning("update the dataset")
                            #datasets_ = mongo_client.videtics.datasets.find_one({"dataset_name":"test_version2"})
                            os.system("git config --global user.email \"anessabiri3@gmail.com\" ")
                            os.system("git config --global user.name \"anessabiri\"")
                            os.system("git commit -m \"First commit  version = " + str(new_version)+ "\"")
                            os.system("git tag -a " +"\""+ str(new_version) +"\" "+  "-m \"first tag\"")
                            os.system("git push --set-upstream origin main")
                            os.system("dvc push")
                            self.logger.warning('dvc pushing done done...')
                            os.chdir(current_directory)
                        else :
                            self.logger.warning('$$$$$$$$$$$$$$$$$$$$ dvc updating ... $$$$$$$$$$$$$$$$$$$$$$$$$$$')
                            os.system("dvc add all")
                            os.system("git add --all")
                            new_version =self.update_version(d["current_version"],cmd['version_type'])
                            dataset = { "dataset_name": d["dataset_name"] }
                            old_version_list = mongo_client.videtics.datasets.find_one({"dataset_name": d["dataset_name"]})["version_list"]
                            old_version_list.append(new_version)
                            newvalues = { "$set": { "current_version": new_version , "latest_version" : new_version , "version_list" : old_version_list } }
                            mongo_client.videtics.datasets.update_one(dataset, newvalues)
                            os.system("git commit -m \"commit  version = " + str(new_version)+ "\"")
                            os.system("git tag -a " +"\""+ str(new_version) +"\" "+  "-m \"first tag\"")
                            os.system("git push ")
                            os.system("dvc push")
                            os.chdir(current_directory)
                        if cmd["afterExportOption"] != "Resize":
                            self.send_response({"commandType" : "taoConvert", "afterExportOption" : cmd["afterExportOption"] ,"convertPath" : '/raid/dataset/dataset_for_tao2/'+str(d["dataset_name"])+'/all/', "trainType" : "person", "current_user" :cmd['current_user']}) 



                    #python3 resize_kitti.py --parent_dir /raid/dataset/detection_dataset/VDSDataset/thermal --dest_dir /raid/dataset/dataset_for_tao/detection/thermal/inverted_included/960-544  --resize 960,544 --keep_aspect_ratio

                    self.send_response({"commandType" : "EndExport", "current_user" :cmd['current_user']})
                    self.logger.warning("######################END RESIZING##########################")
                
            
            time.sleep(.100)