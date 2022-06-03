import os
from PIL import Image, ImageOps
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Pipeline resize for tlt.')
    parser.add_argument('--src_img_dir', type=str, default='')
    parser.add_argument('--dest_img_dir', type=str, default='')
    args = parser.parse_args()
    return args

def inverted_img_it(src_img_path, dest_img_path):
    if not os.path.exists(dest_img_path):
        src_img = Image.open(src_img_path)
        inverted_img = ImageOps.invert(src_img)
        inverted_img.save(dest_img_path)
        return True
    else:
        return False

"""src_img_dir = "/raid/dataset/detection_dataset/VDSDataset2/thermal/PNGImages/"
src_kitti_ann_dir = "/raid/dataset/detection_dataset/VDSDataset2/thermal/Annotations_kitti/"
dest_img_dir = "/raid/dataset/detection_dataset/VDSDataset2/thermal_inverted/PNGImages/"
dest_kitti_ann_dir = "/raid/dataset/detection_dataset/VDSDataset2/thermal_inverted/Annotations_kitti/"""

if __name__ == "__main__":

    args = parse_args()

    src_img_dir = args.src_img_dir+"/PNGImages/"
    src_kitti_ann_dir = args.src_img_dir + "/Annotations_kitti/"
    dest_img_dir = args.src_img_dir + "_inverted/PNGImages/"
    dest_kitti_ann_dir = args.src_img_dir + "_inverted/Annotations_kitti/"

    if not os.path.exists(dest_img_dir):
        os.makedirs(dest_img_dir)
    if not os.path.exists(dest_kitti_ann_dir):
        os.makedirs(dest_kitti_ann_dir)

    for img_filename in os.listdir(src_img_dir):
        xml_filename = img_filename[:-4] + ".txt"
        src_img_path = src_img_dir + img_filename
        src_xml_path = src_kitti_ann_dir + xml_filename
        dest_img_path = dest_img_dir + "inverted_" + img_filename
        dest_xml_path = dest_kitti_ann_dir + "inverted_" + xml_filename
        
        if inverted_img_it(src_img_path, dest_img_path):
        	os.system("cp " + src_xml_path + " " + dest_xml_path)
