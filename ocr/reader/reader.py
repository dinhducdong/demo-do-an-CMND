from vietocr.tool.translate import build_model, translate, translate_beam_search, process_input, predict
from vietocr.tool.utils import download_weights
import cv2
import numpy as np
import matplotlib.pyplot as plt
from keras.preprocessing.image import array_to_img
import math
import torch
from vietocr.tool.config import Cfg
from PIL import Image
import re
from ocr.cropper.cropper import Cropper
from ocr.detector.detector import detect_info
from ocr.core.utils import *
import copy
import statistics
import tensorflow as tf
import torch
from vietocr.tool.predictor import Predictor
#from ocr.reader.predictor import Predictor
"""
=========================
== Reader model
=========================
"""
config = Cfg.load_config_from_name('vgg_transformer')

config['weights'] = 'https://drive.google.com/uc?id=13327Y1tz1ohsm5YZMyXVMPIOjoOA0OaA'
config['device'] = 'cuda:0' if torch.cuda.is_available() else 'cpu'
config['predictor']['beamsearch'] = False
reader = Predictor(config)


def get_text(img):
    img = array_to_img(img)
    text = reader.predict(img)
    text = text.strip('. :')
    return text

def get_dob_text(img):

    h, w, _ = img.shape
    if h < 25:
        ratio = math.ceil(25 / h)
        img = cv2.resize(img, None, fx=ratio, fy=ratio,
                             interpolation=cv2.INTER_CUBIC)
    img = array_to_img(img)
    text = reader.predict(img)
    date = re.findall(r'\d{2}/\d{2}/\d{4}', text)
    if date:
        numbers = re.findall(r'\d', date[0])
    else:
        numbers = re.findall(r'\d', text)
    numbers = numbers[-8:]
    if len(numbers) < 8:
        numbers.extend(['?' for i in range(8 - len(numbers))])
    if numbers[4] != '2':
        numbers[4] = '1'
        numbers[5] = '9'
        if numbers[6] == '0':
            numbers[6] = '9'
    numbers[2:2] = ['/']
    numbers[5:5] = ['/']
    numbers = ''.join(numbers)
    return numbers

def strip_label_and_get_text(img, is_country):
    text = get_text(img)
    colon_index = text.find(':')
    if colon_index != -1 and colon_index < len(text)/2:
        text = text[colon_index+1:]
        text = text.strip()
    else:
        for index, letter in enumerate(text):
            if is_country:
                condition = letter.isupper()
            else:
                condition = letter.isupper() or letter.isdigit()
            if index > 1 and condition:
                text = text[index:]
                break
    return text


def process_list_img(img_list,is_country):
    if len(img_list) == 1:
        return process_first_line(img_list[0],is_country)
    if len(img_list) == 2:
        line1 = process_first_line(img_list[0], is_country)
        line2 = get_text(img_list[1])
        return line1 + '\n' + line2


def process_first_line(img, is_country):
    img_h, img_w, _ = img.shape
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([0, 0, 0])
    upper_blue = np.array([179, 255, 100])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 10))
    morph = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 15))
    thresh = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
    contour_boxes = get_contour_boxes(thresh)
    avg = statistics.mean(map(lambda t: t[-1] * t[-2], contour_boxes))
    boxes_copy = copy.deepcopy(contour_boxes)
    for box in boxes_copy:
        if box[-1] * box[-2] < avg / 3:
            contour_boxes.remove(box)
    contour_boxes.sort(key=lambda t: t[0])
    list_distance = []
    for index, box in enumerate(contour_boxes):
        current_x = box[0] + box[2]
        if index < len(contour_boxes) - 1:
            next_x = contour_boxes[index + 1][0]
            list_distance.append(next_x - current_x)
    avg = statistics.mean(list_distance)
    list_copy = copy.deepcopy(list_distance)
    list_copy.sort(reverse=True)
    if len(list_copy) > 1 and list_copy[0] > 3 * list_copy[1]:
        max_index = list_distance.index(list_copy[0])
        contour_boxes = contour_boxes[max_index + 1:]
        x, y, w, h = find_max_box(contour_boxes)
        img = img[0:img_h, x:img_w]
        return get_text(img)
    else:
        return strip_label_and_get_text(img,is_country)






