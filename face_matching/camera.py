import cv2
from keras.models import load_model
from face_matching.core.utils import *
from bounding_box import bounding_box as bb
from flask import render_template

#face_cascade=cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml")
model = load_model("./model/model_vggface2.keras")
path = "C:\\Users\\kinhk\\PycharmProjects\\DoAnTotNgiep\\app\\static\\idface_images\\ddd2.jpg"
faceid  = extract_face_from_image(path)
yhat1 = get_model_scores(faceid)
print(yhat1)

class Video(object):
    def __init__(self):
        self.video=cv2.VideoCapture(0)
    def __del__(self):
        self.video.release()

    def face_extractor(self, img):
        #faces = face_cascade.detectMultiScale(img, 1.3, 5)
        detector = MTCNN()
        faces = detector.detect_faces(img)
        if faces == '':
            return None
        for face in faces:
            x, y, w, h = face['box']
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 255), 2)
            cropped_face = img[y:y + h, x:x + w]
        return cropped_face
    def get_frame(self):
        ret, image = self.video.read()
        # Resizing image to fit window
        scale_percent = 80  # percent of original size
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
        detector = MTCNN()
        results = detector.detect_faces(image)
        if (results == []):
            cv2.putText(resized_image,"unknown",(10,30), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,255,0),2,cv2.LINE_AA)
            print("Danh sách kết quả trống   ")
            ret, jpeg = cv2.imencode('.jpg', image)
            return jpeg.tobytes()
        print("1. Nhận diện khuôn mặt form hình ảnh")
        x1, y1, width, height = results[0]['box']
        x1, y1 = abs(x1), abs(y1)
        x2, y2 = x1 + width, y1 + height
        # extract the face
        face = image[y1:y2, x1:x2]
        face = self.face_extractor(image)
        print("2. Khuôn mặt được trích xuất")
        if type(face) is np.ndarray:
            face_pixels = cv2.resize(face,(224,224))
            face_pixels = face_pixels.astype('float32')
            samples = preprocess_input(face_pixels)
            yhat2 = model.predict(samples)
            print("3. Embedding khuôn mặt được thu thập")
            print(yhat2)
            text = is_match(yhat1,yhat2)

        ret, jpeg = cv2.imencode('.jpg', image,text)
        return jpeg.tobytes()