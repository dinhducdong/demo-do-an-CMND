import glob
import os
from collections import defaultdict
import numpy as np
import sys, math
from keras.models import load_model
from mtcnn.mtcnn import MTCNN
from matplotlib import pyplot
from PIL import Image
from matplotlib.patches import Rectangle
from matplotlib import pyplot as plt
from keras_vggface.utils import preprocess_input
from scipy.spatial.distance import cosine
from keras_vggface.utils import preprocess_input
from keras_vggface.vggface import VGGFace
from scipy.spatial.distance import cosine

def extract_face_from_image(image_path, required_size=(224, 224)):
  # load image and detect faces
  image = plt.imread(image_path)
  detector = MTCNN()
  faces = detector.detect_faces(image)
  face_images = []
  for face in faces:
      # extract the bounding box from the requested face
      x1, y1, width, height = face['box']
      x2, y2 = x1 + width, y1 + height
      # extract the face
      face_boundary = image[y1:y2, x1:x2]
      # resize pixels to the model size
      face_image = Image.fromarray(face_boundary)
      face_image = face_image.resize(required_size)
      face_array = np.asarray(face_image)
      face_images.append(face_array)
  return face_images

def embedding(path):
    faceid  = extract_face_from_image(path)
    yhat = get_model_scores(faceid)
    return yhat

def remove_file_extension(filename):
    filename = os.path.splitext(filename)[0]
    return filename
def load_embedding():
    embedding_dict = defaultdict()
    for embedding in glob.iglob(pathname='embeddings/*.npy'):
        name = remove_file_extension(embedding)
        dict_embedding = np.load(embedding)
        embedding_dict[name] = dict_embedding
    return embedding_dict

# extract faces and calculate face embeddings for a list of photo files
def get_embeddings(filenames, model, embedding_path):
    # extract faces
    faces = [extract_face_from_image(f) for f in filenames]
    # convert into an array of samples
    samples = np.asarray(faces, 'float32')
    # prepare the face for the model, e.g. center pixels
    samples = preprocess_input(samples)
    # perform prediction
    yhat = model.predict(samples)
    path = os.path.join(embedding_path, str(filenames))
    try:
        np.save(path, yhat)
    except Exception as e:
        print(str(e))
    return yhat
# determine if a candidate face is a match for a known face
def is_match(known_embedding, candidate_embedding, thresh=0.5):
    # calculate distance between embeddings
    score = cosine(known_embedding, candidate_embedding)
    if score <= thresh:
        return "match"
    else:
        return "nomatch"
def get_model_scores(faces):
    samples = np.asarray(faces, 'float32')
    # prepare the data for the model
    samples = preprocess_input(samples, version=2)

    # create a vggface model object
    model = VGGFace(model='resnet50',
      include_top=False,
      input_shape=(224, 224, 3),
      pooling='avg')
    return model.predict(samples)
def highlight_faces(faces):

    ax = plt.gca()

    # for each face, draw a rectangle based on coordinates
    for face in faces:
        x, y, width, height = face['box']
        face_border = Rectangle((x, y), width, height,
                          fill=False, color='red')
        ax.add_patch(face_border)
    plt.show()
try :
    model = load_model("./model/model_vggface2.keras")
except:
    from keras_vggface.vggface import VGGFace
    model = VGGFace(model='resnet50', include_top=False, input_shape=(224, 224, 3), pooling='avg')
    model.save("./model/model_vggface2.keras")
