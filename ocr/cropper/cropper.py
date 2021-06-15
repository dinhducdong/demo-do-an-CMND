import cv2
import numpy as np
from imutils.perspective import four_point_transform
from math import sqrt
import imutils
from PIL import Image
from skimage.filters import threshold_local
import matplotlib.pyplot as plt
#from ocr.core.utils import four_point_transform
ratio = 1
class Cropper:
    TARGET_SIZE = (416, 416)
    IMAGE_SIZE = (1920, 1200)

    def __init__(self):
        self.image_output = None
    def align_image(self, img):
        image = img.copy()
        blur = cv2.GaussianBlur(image, (5, 5), 0)
        hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
        # lay vien mau xanh cua anh
        lower_blue = np.array([60, 0, 0])
        upper_blue = np.array([106, 255, 255])
        mask = cv2.inRange(hsv, lower_blue, upper_blue)
        mask = cv2.Canny(mask, 140, 150)
        #if show_mask == True: cv2.imshow("Mask Image", imutils.resize(mask, width=646, height=408))
        kernel = np.ones((5, 5))
        # phep co gian anh
        imgDial = cv2.dilate(mask, kernel, iterations=9)
        imgThre = cv2.erode(imgDial, kernel, iterations=8)
        # contours anh
        contours, _ = cv2.findContours(imgThre, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        # Tìm ra diện tích của toàn bộ các contours
        area_cnt = [cv2.contourArea(cnt) for cnt in contours]
        area_sort = np.argsort(area_cnt)[::-1]
        # Trích xuất contours lớn nhất
        cnt = contours[area_sort[0]]
        # draw contours len anh va hien thi
        screenCnt = None
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4:
            screenCnt = approx
        #cv2.drawContours(image, [screenCnt], -1, (0, 255, 0), 3)
        #if show_draw == True: cv2.imshow("draw Contours", imutils.resize(image, width=646, height=408))
        warped = four_point_transform(img, screenCnt.reshape(4, 2) * ratio)
        # warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        # T = threshold_local(warped, 11, offset=10, method="gaussian")
        # warped = (warped > T).astype("uint8") * 255
        #if show_crop == True: cv2.imshow("Crop image", imutils.resize(warped, width=646, height=408))

        warped = imutils.resize(warped, width=646,height=408)
        return warped

    def set_image(self, original_image):
        self.image_output = self.align_image(original_image)