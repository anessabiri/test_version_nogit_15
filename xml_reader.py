import sys
import os
import csv
from os.path import isfile, isdir, join, dirname, splitext, basename, abspath
import xml.etree.ElementTree as ET
from PIL import Image
import logging


class XMLReader:
    def __init__(self, path, path_img, task_name, path_export):
        self.logger = logging.getLogger(__name__)
        file = open(path, 'r')
        self.dict_translation = {
            "véhicule léger" : "lightVehicle",
            "véhicule intermediaire" : "intermediateVehicle",
            "poids lourd" : "heavyVehicle",
            "moto" : "motorcycle",
            "vélo" : "bicycle",
            "personne" : "person",
            "trotinette" : "scooter",
            "chien" : "dog",
            "visage" : "face",
            "Face" : "face",
            "tramway" : "tramway",
            "truck" : "heavyVehicle",
            "van" : "intermediateVehicle",
            "car" : "lightVehicle",
            "pickup" : "lightVehicle",
            "motorbike" : "motorcycle"
        }
        self.dict_translation2 = {
            "citadine" : "citycar",
            "berline" : "sedan",
            "coupé" : "coupe",
            "cabriolet" : "convertible",
            "break" : "stationwagon",
            "monospace" : "monospace",
            "minibus" : "minibus",
            "SUV" : "suv",
            "pickup" : "pickup",
            "petit utilitaire" : "smallvan",
            "remorque" : "trailer",
            "camionette" : "van",
            "utilitaire 20m3" : "van20m3",
            "fourgon blindé" : "armoredtruck",
            "utilitaire benne" : "vanwagon",
            "caravane" : "caravan",
            "camping car" : "campingcar",
            "bus" : "bus",
            "camion benne" : "truckwagon",
            "camion citerne" : "tankertruck",
            "camion transport" : "transporttruck",
            "pl3 camion autoroutier" : "pl3highwaytruck",
            "pl3 grand autocar" : "pl3bus",
            "pl3 camion citerne" : "pl3tankertruck",
            "inconnu" : "unknown"
        }

        self.dict_translation3 = {
            "gris" : "gray",
            "noir" : "black",
            "blanc" : "white",
            "rouge" : "red",
            "bleu" : "blue",
            "vert" : "green",
            "violet" : "purple",
            "orange" : "orange",
            "jaune" : "yellow",
            "rose" : "pink",
            "marron" : "brown"
        }
        self.path = path
        self.path_img = path_img
        self.task_name = task_name
        self.path_export = path_export
        self.content = file.read()
        if len(self.content) == 0:
            self.root = None
        else:
            self.root = ET.fromstring(self.content)
        self.template = "{name} 0.00 0 0.0 {xmin:.3f} {ymin:.3f} {xmax:.3f} {ymax:.3f} 0.0 0.0 0.0 0.0 0.0 0.0 0.0"
        self.list_class = ["car", "truck", "trailer", "van", "bicycle", "motorbike", "person", "bus"]

    def get_filename(self):
        return splitext(basename(self.path))[0]

    def get_dir(self):
        return dirname(self.path)


class XMLReaderForKitti(XMLReader):
    def __init__(self, path, path_img, task_name, path_export):
        super().__init__(path, path_img, task_name, path_export)

    def get_objects(self, sf, option_key, option):
        if self.root is None: return []
        scale_x = sf[0]
        scale_y = sf[1]

        width = float(self.root.findall("size")[0].find('width').text)
        height = float(self.root.findall("size")[0].find('height').text)

        objects = []
        if option_key == 'detection':
            for idx, option_class in enumerate(option):
                if option_class in self.dict_translation:
                    option[idx] = self.dict_translation[option_class]
            for object in self.root.findall("object"):
                name = object.find("name").text
                name = name if name not in self.dict_translation else self.dict_translation[name]
                if name in option:
                    x_min = max(0.0, float(object.find("bndbox").find("xmin").text)) * scale_x
                    y_min = max(0.0, float(object.find("bndbox").find("ymin").text)) * scale_y
                    x_max = min(width, float(object.find("bndbox").find("xmax").text)) * scale_x
                    y_max = min(height, float(object.find("bndbox").find("ymax").text)) * scale_y
                    name = name if name not in self.dict_translation else self.dict_translation[name]
                    if name == "heavyVehicle":
                        for attribute in object.find("attributes").findall("attribute"):
                            att = attribute.find("name").text
                            if att == "Type":
                                candidate_name = self.dict_translation2[attribute.find("value").text]
                                if candidate_name == "bus":
                                    name = "bus"

                    objects.append({
                        "name" : name,
                        "xmin" : x_min,
                        "ymin" : y_min,
                        "xmax" : x_max,
                        "ymax" : y_max
                    })
        elif option_key == 'attribute_to_detection':
            del_option_class = []
            for key_name in option:
                if option_class in self.dict_translation:
                    option[self.dict_translation[option_class]] = option[option_class]
                    del_option_class.append(option_class)
            for option_class in del_option_class:
                del option[option_class]
            for object in self.root.findall("object"):
                name = object.find("name").text
                name = name if name not in self.dict_translation else self.dict_translation[name]
                if name in option:
                    if option[name] is not None:
                        for attribute in object.find("attributes").findall("attribute"):
                            att = attribute.find("name").text
                            if att == option[name]:
                                name = self.dict_translation2[attribute.find("value").text]
                    x_min = max(0.0, float(object.find("bndbox").find("xmin").text)) * scale_x
                    y_min = max(0.0, float(object.find("bndbox").find("ymin").text)) * scale_y
                    x_max = min(width, float(object.find("bndbox").find("xmax").text)) * scale_x
                    y_max = min(height, float(object.find("bndbox").find("ymax").text)) * scale_y
                    name = name if name not in self.dict_translation else self.dict_translation[name]
                    objects.append({
                        "name" : name,
                        "xmin" : x_min,
                        "ymin" : y_min,
                        "xmax" : x_max,
                        "ymax" : y_max
                    })

        return objects

    def fill_template(self, object):
        return self.template.format(**object)

    def export_kitti(self, option):
  
        sf = (1.0, 1.0)

        option_main_key = list(option.keys())[0]
        objects = self.get_objects(sf, option_main_key, option[option_main_key])

        export_folder = self.path_export
        if not os.path.exists(join(export_folder, "Annotations_kitti/")):
            os.system("mkdir " + join(export_folder, "Annotations_kitti").replace(' ', '\ '))

        if len(objects) == 0:
            os.system("touch " + join(export_folder, "Annotations_kitti/" + self.task_name.replace(' ', '_') + '_' + self.get_filename()) + ".txt")
              
        else:
            file = open(join(export_folder, "Annotations_kitti/" + self.task_name.replace(' ', '_') + '_' + self.get_filename()) + ".txt", 'w')
            
            for object in objects[:-1]:
                if len(self.fill_template(object).split(' ')) != 15:
                    print(self.fill_template(object))
                file.write(self.fill_template(object) + "\n")
            
            # Write last without '\n'
            if len(self.fill_template(objects[-1]).split(' ')) != 15:
                print(self.fill_template(objects[-1]))
            file.write(self.fill_template(objects[-1]))

            file.close()
            
        export_folder = self.path_export
        if not os.path.exists(join(export_folder, "PNGImages/")):
            os.system("mkdir " + join(export_folder, "PNGImages"))
        print(self.path_img.replace(' ', '\ '))
        os.system('cp ' + (self.path_img.replace(' ', '\ ')) + ' ' + (join(export_folder, "PNGImages/"+ self.task_name.replace(' ', '_') + '_' + self.get_filename() + '.PNG').replace(' ', '\ ')))

        return True


class XMLReaderForIdTracking(XMLReader):
    def __init__(self, path, path_img, task_name, path_export):
        super().__init__(path, path_img, task_name, path_export)

    def get_crop_parameters(self, sf, option_key, option):
        if self.root is None: return []
        scale_x = sf[0]
        scale_y = sf[1]

        width = float(self.root.findall("size")[0].find('width').text)
        height = float(self.root.findall("size")[0].find('height').text)

        crop_parameters_list = []
        for idx, option_class in enumerate(option):
            if option_class in self.dict_translation:
                option[idx] = self.dict_translation[option_class]
        for object in self.root.findall("object"):
            name = object.find("name").text
            name = name if name not in self.dict_translation else self.dict_translation[name]
            if name in option:
                x_min = max(0.0, float(object.find("bndbox").find("xmin").text)) * scale_x
                y_min = max(0.0, float(object.find("bndbox").find("ymin").text)) * scale_y
                x_max = min(width, float(object.find("bndbox").find("xmax").text)) * scale_x
                y_max = min(height, float(object.find("bndbox").find("ymax").text)) * scale_y
                name = name if name not in self.dict_translation else self.dict_translation[name]
                for attribute in object.find("attributes").findall("attribute"):
                    att = attribute.find("name").text
                    if att == "track_id":
                        track_id = attribute.find("value").text
                        crop_parameters_list.append([name, (x_min, y_min, x_max, y_max), track_id])
                        break

        return crop_parameters_list


    def export_id_tracking(self, option):
  
        sf = (1.0, 1.0)

        option_main_key = list(option.keys())[0]
        crop_parameters_list = self.get_crop_parameters(sf, option_main_key, option[option_main_key])

        export_folder = self.path_export
        if not os.path.exists(join(export_folder, "CropById/")):
            os.system("mkdir " + join(export_folder, "CropById"))
        if not os.path.exists(join(export_folder, "CropById/" + self.task_name)):
            os.system("mkdir " + join(export_folder, "CropById/" + self.task_name))


        origin_img = Image.open(self.path_img)

        for class_name, bbox, track_id in crop_parameters_list:
            if not os.path.exists(join(export_folder, "CropById/" + self.task_name + "/" + class_name)):
                os.system("mkdir " + join(export_folder, "CropById/" + self.task_name + "/" + class_name))
            if not os.path.exists(join(export_folder, "CropById/" + self.task_name + "/" + class_name + "/" + track_id)):
                os.system("mkdir " + join(export_folder, "CropById/" + self.task_name + "/" + class_name + "/" + track_id))
            
            im_crop = origin_img.crop(bbox)
            im_crop.save(join(export_folder, "CropById/" + self.task_name + "/" + class_name + "/" + track_id) + "/" + self.path_img.split('/')[-1])

        return True


class XMLReaderForSimpleAttribute(XMLReader):
    def __init__(self, path, path_img, task_name, path_export):
        super().__init__(path, path_img, task_name, path_export)

    def get_crop_parameters(self, sf, option):
        if self.root is None: return []
        scale_x = sf[0]
        scale_y = sf[1]

        width = float(self.root.findall("size")[0].find('width').text)
        height = float(self.root.findall("size")[0].find('height').text)

        crop_parameters_list = []
        for object in self.root.findall("object"):
            name_origin = object.find("name").text
            name = name_origin if name_origin not in self.dict_translation else self.dict_translation[name_origin]
            if name_origin in option:
                x_min = min(max(0.0, float(object.find("bndbox").find("xmin").text)), width) * scale_x
                y_min = min(max(0.0, float(object.find("bndbox").find("ymin").text)), height) * scale_y
                x_max = max(min(width, float(object.find("bndbox").find("xmax").text)), 0.0) * scale_x
                y_max = max(min(height, float(object.find("bndbox").find("ymax").text)), 0.0) * scale_y
                for attribute in object.find("attributes").findall("attribute"):
                    att = attribute.find("name").text
                    if att == option[name_origin]:
                        att_txt = self.dict_translation3[attribute.find("value").text]
                        crop_parameters_list.append([(x_min, y_min, x_max, y_max), att_txt])
                        break

        return crop_parameters_list


    def export_simple_attribute(self, option):
  
        sf = (1.0, 1.0)

        crop_parameters_list = self.get_crop_parameters(sf, option["simple_attribute"])

        export_folder = self.path_export
        if not os.path.exists(join(export_folder, "CropBySimpleAtt/")):
            os.system("mkdir " + join(export_folder, "CropBySimpleAtt"))

        try:
            origin_img = Image.open(self.path_img)
        except:
            origin_img = Image.open(self.path_img.replace(".PNG", ".jpg"))

        for idx, (bbox, att_class) in enumerate(crop_parameters_list):
            if not os.path.exists(join(export_folder, "CropBySimpleAtt/" + att_class)):
                os.system("mkdir " + join(export_folder, "CropBySimpleAtt/" + att_class))
            
            try :
                im_crop = origin_img.crop(bbox)
                im_crop.save(join(export_folder, "CropBySimpleAtt/" + att_class + "/" + self.task_name + "_" + str(idx) + "_" + self.path_img.split('/')[-1]))
            except:
                self.logger.warning("CROP PASSED")

        return True

class XMLReaderForComposedAttributes(XMLReader):
    def __init__(self, path, path_img, task_name, path_export, csv_writer):
        super().__init__(path, path_img, task_name, path_export)
        self.csv_writer = csv_writer
        self.dict_translation_apr = {"color_down" : "lower_body_color",
                                        "color_up" : "upper_body_color",
                                        "up sleeves" : "sleeves_up",
                                        "down length" : "down_length"}
        
    def get_crop_parameters(self, sf, option_key, option):
        if self.root is None: return []
        scale_x = sf[0]
        scale_y = sf[1]

        width = float(self.root.findall("size")[0].find('width').text)
        height = float(self.root.findall("size")[0].find('height').text)

        crop_parameters_list = []
        for idx, option_class in enumerate(option):
            if option_class in self.dict_translation:
                option[idx] = self.dict_translation[option_class]
        for object in self.root.findall("object"):
            name = object.find("name").text
            name = name if name not in self.dict_translation else self.dict_translation[name]
            att_dict = {}
            bool_dict = {"False" : "no", "True" : "yes"}
            if name in option:
                x_min = max(0.0, float(object.find("bndbox").find("xmin").text)) * scale_x
                y_min = max(0.0, float(object.find("bndbox").find("ymin").text)) * scale_y
                x_max = min(width, float(object.find("bndbox").find("xmax").text)) * scale_x
                y_max = min(height, float(object.find("bndbox").find("ymax").text)) * scale_y
                name = name if name not in self.dict_translation else self.dict_translation[name]
                for attribute in object.find("attributes").findall("attribute"):
                    att = attribute.find("name").text
                    if att == "track_id":
                        track_id = attribute.find("value").text
                        crop_parameters_list.append([name, (x_min, y_min, x_max, y_max), track_id])
                        att_dict["fname"] = self.task_name + "_" + track_id + "_" + self.path_img.split('/')[-1]
                    else:
                        sanitized_att = self.dict_translation_apr[att] if att in self.dict_translation_apr else att
                        or_att = attribute.find("value").text
                        att_value = or_att if or_att not in  bool_dict else bool_dict[or_att]
                        att_dict[sanitized_att] = att_value
                self.csv_writer.writerow(att_dict)

        return crop_parameters_list


    def export_composed_attributes(self, option):
  
        sf = (1.0, 1.0)

        option_main_key = list(option.keys())[0]
        crop_parameters_list = self.get_crop_parameters(sf, option_main_key, option[option_main_key])

        export_folder = self.path_export
        if not os.path.exists(join(export_folder, "images/")):
            os.system("mkdir " + join(export_folder, "images"))
        # if not os.path.exists(join(export_folder, "CropById/" + self.task_name)):
        #     os.system("mkdir " + join(export_folder, "CropById/" + self.task_name))


        origin_img = Image.open(self.path_img)

        for class_name, bbox, track_id in crop_parameters_list:

        #     if not os.path.exists(join(export_folder, "CropById/" + self.task_name + "/" + class_name)):
        #         os.system("mkdir " + join(export_folder, "CropById/" + self.task_name + "/" + class_name))
        #     if not os.path.exists(join(export_folder, "CropById/" + self.task_name + "/" + class_name + "/" + track_id)):
        #         os.system("mkdir " + join(export_folder, "CropById/" + self.task_name + "/" + class_name + "/" + track_id))
            
            im_crop = origin_img.crop(bbox)
            # self.logger.warning("###############################################################################################################")
            # self.logger.warning(join(export_folder, "images/") + self.task_name + "_" + track_id + "_" + self.path_img.split('/')[-1])
            im_crop.save(join(export_folder, "images/") + self.task_name + "_" + track_id + "_" + self.path_img.split('/')[-1])

        return True
