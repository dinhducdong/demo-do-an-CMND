import cv2
from keras.models import load_model
from face_matching.core.utils import *
from bounding_box import bounding_box as bb
from flask import render_template
#face_cascade=cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml")

model = load_model("./model/model_vggface2.keras")
def faceid(path):
    faceid  = extract_face_from_image(path)
    yhat = get_model_scores(faceid)
    return yhat


