import os
import argparse

from tqdm import tqdm
from PIL import Image
from pathlib import Path


def change_ann(line, width, height, new_width, new_height, offset):
    line_split = line.split(' ')
    xmin = float(line_split[4]) / width
    ymin = float(line_split[5]) / height
    xmax = float(line_split[6]) / width
    ymax = float(line_split[7]) / height
    
    line_split[4] = str("%.3f" % ((xmin * new_width) + offset[0]))
    line_split[5] = str("%.3f" % ((ymin * new_height) + offset[1]))
    line_split[6] = str("%.3f" % ((xmax * new_width) + offset[0]))
    line_split[7] = str("%.3f" % ((ymax * new_height) + offset[1]))

    return " ".join(line_split)

def keep_aspect_ratio_func(annotation_directory, new_annotation_directory, new_img_directory, img, image_name, desired_width, desired_height, new_img_directory_data, new_annotation_directory_data):
    width, height = img.size
    
    ratio_w = desired_width/width
    ratio_h = desired_height/height
    if ratio_h < ratio_w:
        resized_img = img.resize((int(width*ratio_h), int(height*ratio_h)))
        new_im = Image.new("RGB", (desired_width, desired_height))
        offset = (int((desired_width-resized_img.width)/2), 0)
        new_im.paste(resized_img, offset)
    elif ratio_h > ratio_w:
        resized_img = img.resize((int(width*ratio_w), int(height*ratio_w)))
        new_im = Image.new("RGB", (desired_width, desired_height))
        offset = (0, int((desired_height-resized_img.height)/2))
        new_im.paste(resized_img, offset)
    else:
        resized_img = img.resize((int(width*ratio_w), int(height*ratio_w)))
        new_im = Image.new("RGB", (desired_width, desired_height))
        offset = (0, 0)
        new_im.paste(resized_img, offset)
    
    
    if ".png" in image_name:
        annotation_name = image_name.replace(".png", ".txt")
    elif ".PNG" in image_name:
        annotation_name = image_name.replace(".PNG", ".txt")
    else:
        annotation_name = image_name.replace(".jpg", ".txt")

    new_line_list = []
    if os.path.exists(os.path.join(annotation_directory, annotation_name)):
        with open(os.path.join(annotation_directory, annotation_name), "r") as f:
            for line in f:
                if line != "\n":
                    new_line = change_ann(line, width, height, resized_img.width, resized_img.height, offset)
                    new_line_list.append(new_line)
    
        with open(os.path.join(new_annotation_directory, annotation_name), "w") as f:
            for new_line in new_line_list:
                f.write(new_line)
        
        # with open(os.path.join(new_annotation_directory_data, annotation_name), "w") as f:
        #     for new_line in new_line_list:
        #         f.write(new_line)
    else:
        Path(os.path.join(new_annotation_directory, annotation_name)).touch()
        # Path(os.path.join(new_annotation_directory_data, annotation_name)).touch()
    if ".png" in image_name:
        image_name = image_name.replace(".png", ".jpg")
    elif ".PNG" in image_name:
        image_name = image_name.replace(".PNG", ".jpg")

    new_im.save(os.path.join(new_img_directory, image_name))
    # new_im.save(os.path.join(new_img_directory_data, image_name))
    
    return new_im, new_line_list

def parse_args():
    parser = argparse.ArgumentParser(description='Pipeline resize for tlt.')
    parser.add_argument('--parent_dir', type=str, default='', help='Parent directory.')
    parser.add_argument('--dest_dir', type=str, default='')
    parser.add_argument('--base_name', type=str, default='', help='Base name for folder.')
    parser.add_argument('--resize', type=str, default='', help='Size to be resize.')
    parser.add_argument('--keep_aspect_ratio', dest='keep_aspect_ratio', default=False, action='store_true')
    args = parser.parse_args()
    return args


def strech_img(img, image_name, annotation_directory, new_img_directory, new_annotation_directory):

    width, height = img.size

    resized_img = image.resize((desired_width, desired_height))
    if ".png" in image_name:
        image_name = image_name.replace(".png", ".jpg")
    
    resized_img.save(os.path.join(new_img_directory, image_name))
    
    annotation_name = image_name.split('.')[0] + ".txt"

    new_line_list = []
    if os.path.exists(os.path.join(annotation_directory, annotation_name)):
        with open(os.path.join(annotation_directory, annotation_name), "r") as f:
            for line in f:
                if line != "\n":
                    new_line = change_ann(line, width, height, desired_width, desired_height, offset=[0.0, 0.0])
                    new_line_list.append(new_line)
    
        with open(os.path.join(new_annotation_directory, annotation_name), "w") as f:
            for new_line in new_line_list:
                f.write(new_line)
        
    else:
        Path(os.path.join(new_annotation_directory, annotation_name)).touch()


if __name__ == "__main__":
    args = parse_args()
    parent_dir = args.parent_dir
    base_name = args.base_name
    keep_aspect_ratio = args.keep_aspect_ratio
    desired_width = int(args.resize.split(',')[0])
    desired_height = int(args.resize.split(',')[1])

    img_directory = os.path.join(parent_dir, "PNGImages")  # _" + base_name)
    annotation_directory = os.path.join(parent_dir, "Annotations_kitti")  # + base_name)
    ann_list = os.listdir(annotation_directory)
    
    image_list = os.listdir(img_directory)
    
    # new_img_directory = "/home/videtics/tlt_experiments/dataset/villa_visible/960-540/img/"
    new_img_directory = os.path.join(args.dest_dir, "img")
    # new_img_directory = "/home/videtics/tlt_experiments/dataset/port-cannes/960-540/img/"
    # new_img_directory = "/home/videtics/tlt_experiments/dataset/villa_thermal/704-576/img/"
    # new_img_directory_data = os.path.join(parent_dir, "img_" + str(desired_width) + "-" + str(desired_height))
    # new_img_directory = os.path.join(parent_dir, "img_" + base_name + "_" + str(desired_width) + "-" + str(desired_height))
    # new_annotation_directory = "/home/videtics/tlt_experiments/dataset/villa_thermal/704-576/ann/"
    # new_annotation_directory = "/home/videtics/tlt_experiments/dataset/villa_visible/960-540/ann/"
    new_annotation_directory = os.path.join(args.dest_dir, "ann")
    # new_annotation_directory = "/home/videtics/tlt_experiments/dataset/port-cannes/960-540/ann/"
    # new_annotation_directory_data = os.path.join(parent_dir, "ann_" + str(desired_width) + "-" + str(desired_height))
    # new_annotation_directory = os.path.join(parent_dir, "ann_"+ base_name + "_" + str(desired_width) + "-" + str(desired_height))

    if not os.path.exists(new_img_directory):
        os.makedirs(new_img_directory)
    
    if not os.path.exists(new_annotation_directory):
        os.makedirs(new_annotation_directory)
    
    # if not os.path.exists(new_img_directory_data):
    #     os.makedirs(new_img_directory_data)
    
    # if not os.path.exists(new_annotation_directory_data):
    #     os.makedirs(new_annotation_directory_data)

    for image_name in tqdm(image_list):
        # image_name = ann_name.replace(".txt", ".png")  # png in certain case ...
        
        image = Image.open(os.path.join(img_directory, image_name))
        width, height = image.size
        same_ratio = (width/height) == (desired_width/desired_height)
            
        if keep_aspect_ratio:
            keep_aspect_ratio_func(annotation_directory, new_annotation_directory, new_img_directory, image, image_name, desired_width, desired_height, new_img_directory_data='', new_annotation_directory_data='')
        else:
            strech_img(image, image_name, annotation_directory, new_img_directory, new_annotation_directory)

