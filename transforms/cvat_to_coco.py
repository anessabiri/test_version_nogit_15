# Copyright 2021 Videtics
# Authors : cyril

import os, sys
import json

import xml.etree.ElementTree as ET

labels_trad = {
'bras levés' : 'arms_raised',
'combat' : 'fighting',
'action' : 'action',
'aucune' : 'none',
'se lever' : 'stand_up',
'se baisser' : 'bend_down',
's\'assoir' : 'sit_down',
'se coucher' : 'lie_down',
'chuter' : 'falling',
'déplacement' : 'movement',
'stationnaire' : 'stationary',
'lent' : 'slow',
'normal' : 'normal',
'rapide' : 'fast',
'posture' : 'posture',
'debout' : 'standing',
'assis sur un objet' : 'sitting_on_object',
'assis au sol' : 'sitting_on_ground',
'allongé' : 'lying_down',
'à genoux' : 'kneeling',
'penché' : 'bending',
'anormal' : 'unnatural',
'autre' : 'other',
'accroupi' : 'squatting',
'gestes' : 'gesture',
'aucuns' : 'none',
'false' : 'false',
'true' : 'true'
}

def add_track_to_coco_annotations(track, annotations, area):
    k = 0
    n_track = len(annotations)
    for pose in track["poses"]:
        if pose["fully_occluded"] == "0":
            annotation = {}
            
            annotation["keypoints"] = pose["keypoints"]
            annotation["image_id"] = pose["image_id"]
            
            annotation["id"] = n_track + k
            annotation['iscrowd'] = 0
            annotation['area'] = area
            annotations.append(annotation)
            k+=1

def add_track_to_action_annotations(track, annotations):
    k = 0
    n_track = len(annotations)
    track_annotations = {}
    track_annotations["poses"] = []
    for pose in track["poses"]:
        annotation = pose
        del annotation['fully_occluded']
        annotation["category_id"] = 1
        annotation["id"] = n_track + k
        annotation["num_keypoints"] = 14
        track_annotations["poses"].append(annotation)
        k+=1
    annotations.append(track_annotations)


def add_xml_to_data(images, coco_annotations, action_annotations, xml_path):
    '''
    Add datas from a xml to a dictionnary, empty at first
    :param dic Dictionary : target dictionary
    :param xml_path str : input data xml path
    '''

    tree = ET.parse(xml_path)
    root = tree.getroot()

    n_images = len(images)
    k=0

    video_name = root.find("meta").find("task").find("name").text
    width, height = root.find("meta").find("task").find("original_size").find("width").text, root.find("meta").find("task").find("original_size").find("height").text
    for child in root:
        if child.tag == "track":
            track_info = {}
            track_info["width"], track_info["height"] = width, height 
            track_info["poses"] = []
            for points in child:
                frame = int(points.attrib["frame"])
                image_id = n_images + frame

                if frame > k - 1 :
                    
                    frame_id = str(frame).zfill(6)
                    image = {}
                    image["file_name"] = video_name.split(".")[0] + "_frame_" + frame_id + ".png"
                    image["width"] = width
                    image["height"] = height
                    image["id"] = image_id
                    images.append(image)
                    k+=1
                pose = {}
                pose["keypoints"] = convert_points_format(points.attrib["points"])
                pose["image_id"] = image_id
                pose["labels"] = {}
                for pose_attrib in points:

                    pose["labels"][labels_trad[pose_attrib.attrib["name"]]] = labels_trad[pose_attrib.text]
                
                pose["fully_occluded"] = points.attrib["occluded"]
                
                track_info["poses"].append(pose)      
            
            add_track_to_coco_annotations(track_info, coco_annotations, int(width) * int(height) )
            add_track_to_action_annotations(track_info,action_annotations )


def convert_points_format(points_str):
    new_str = points_str.replace(";", ",").split(",")
    str_keypoints = new_str[0:28]
    str_mask = new_str[28:42]
    keypoints = []
    for k in range(0,len(str_keypoints), 2):
        if k < 28:
            keypoints.append(float(str_keypoints[k]))
            keypoints.append(float(str_keypoints[k+1]))
            keypoints.append(2) # visibility
    for k in range(len(str_mask)):
        mask_value = int(float(str_mask[k]))
        if mask_value == 2:
            keypoints[3*k + 2] = 1.1
        elif mask_value == 1:
            keypoints[3*k + 2] = 1.2
    return keypoints

def to_json_coco(images, annotations_coco):
    coco_dic = {}
    coco_dic["images"] = images
    coco_dic["annotations"] = annotations_coco

    keypoints_categorie = {}
    keypoints_categorie["supercategory"] = "person"
    keypoints_categorie["id"] = 1
    keypoints_categorie["name"] = "person"
    keypoints_categorie["keypoints"] = ["head", "neck", "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist", "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]
    keypoints_categorie["skeleton"] = [[0,1],[1,2],[1,3],[2,4],[3,5],[4,6],[5,7],[1,8],[1,9],[8,10],[9,11], [10,12],[11,13]]
    coco_dic["categories"] = [keypoints_categorie]


    print("{} images, {} annotations".format(len(coco_dic["images"]), len(coco_dic["annotations"])))
    return coco_dic

if __name__ == '__main__':
    images, coco_annotations, action_annotations = [], [], []
    add_xml_to_data(images, coco_annotations, action_annotations, sys.argv[1])
    add_xml_to_data(images, coco_annotations, action_annotations, sys.argv[2])
    add_xml_to_data(images, coco_annotations, action_annotations, sys.argv[3])
    add_xml_to_data(images, coco_annotations, action_annotations, sys.argv[4])

    print(len(coco_annotations))
    
    json_tasks_coco = to_json_coco(images, coco_annotations)
    with open(sys.argv[5], "w") as outfile: 
        json.dump(json_tasks_coco, outfile, indent=None)
    
    json_tasks_actions = to_json_coco(images, action_annotations)
    with open(sys.argv[6], "w") as outfile: 
        json.dump(json_tasks_actions, outfile, indent=None)
