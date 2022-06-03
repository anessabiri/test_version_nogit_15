import sys
from os import listdir
from os.path import isfile, isdir, join, dirname, splitext, basename, abspath
import xml.etree.ElementTree as ET
from PIL import Image


def get_directory_xml_files(dir):
    return [join(dir, f) for f in listdir(dir) if isfile(join(dir, f)) and splitext(f)[1].lower() == ".xml"]

def get_directory_img_files(dir):
    return [join(dir, f) for f in listdir(dir) if isfile(join(dir, f)) and (splitext(f)[1].lower() == ".PNG" or splitext(f)[1].lower() == ".png" or splitext(f)[1].lower() == ".jpg")]