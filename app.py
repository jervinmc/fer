from keras.preprocessing.image import img_to_array
import imutils
import cv2
from keras.models import load_model
import numpy as np
import os
from Database import Database
import schedule


currentLabel = ''
def predict():
    db = Database()
    data = db.query(f"select name from clusters order by value desc")
    if(data[0][0]==globals()['currentLabel']):
        print(f"predict:{data[1][0]}")
    else:
        print(f"predict:{data[0][0]}")
    pass

schedule.every(1).minutes.do(predict)

def updateCluster(name):
    db = Database()
    db.insert(f"UPDATE clusters set value=value+1 where name='{name}'")
    pass

#TO IGNORE THE WARNINGS
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

#HAARCASCADE DATA
detection_model_path = 'haarcascade_files/haarcascade_frontalface_default.xml'

#SAMPLE CNN
emotion_model_path = 'models/_mini_XCEPTION.102-0.66.hdf5'


#IMPORTING THE DATASETS FROM HAARCASCADE
face_detection = cv2.CascadeClassifier(detection_model_path)

#PARA MAKITA NATIN YUNG FORMULATE NG MALAPIT NA VALUE, SINCE SI CNN AY BINABASA NYA YUNG MGA MAGKAKALAPIT NA VALUE FROM HAARCASCADE DATASETS
emotion_classifier = load_model(emotion_model_path, compile=False)

#NAGLAGAY TAYO FOR LIST LANG NG NEED NATIN AND IENUMARATE BASED SA PAGKAKASUNODSUNOD NA PAG SETUP NATIN NG PREDICTION SA DATASETS
EMOTIONS = ["angry" ,"disgust","scared", "happy", "sad", "surprised",
 "neutral"]


cv2.namedWindow('Actual')

#PAG SETUP NG VIDEOCAPTURE NA CAMERA
camera = cv2.VideoCapture(0)

#READING OF EVERY FRAME NG CV2
while True:
    schedule.run_pending()
    ret,frame = camera.read()  
    #RESIZING NA FRAME
    frame = imutils.resize(frame,width=300)
    #WE USED GRAY TO KEEP THE IMAGES TO BECOME BLACK AND WHITE PARA MAS MADALING MATANGGAL ANG NOISE BACKGROUND
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    #CALLING THE FUNCTION PARA MA TRIGGER YUNG DETECTION NATIN SA MUKHA
    faces = face_detection.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=5,minSize=(30,30),flags=cv2.CASCADE_SCALE_IMAGE)
    
    #TO CREATE AN ARRAY AS ZERO
    canvas = np.zeros((250, 300, 3), dtype="uint8")

    #CLONING NG FRAME NATIN FOR 
    frameCopy = frame.copy()

    #A PROCESS NA PAG MAY NAKITANG FACES.
    if len(faces) > 0:
        faces = sorted(faces, reverse=True,
        key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))[0]
        (fX, fY, fW, fH) = faces
        roi = gray[fY:fY + fH, fX:fX + fW]
        roi = cv2.resize(roi, (64, 64))
        roi = roi.astype("float") / 255.0
        roi = img_to_array(roi)
        roi = np.expand_dims(roi, axis=0)
        preds = emotion_classifier.predict(roi)[0]
        emotion_probability = np.max(preds)
        label = EMOTIONS[preds.argmax()]
        globals()['currentLabel']=label
        updateCluster(label)
    else: continue

    #PAG GAWA NATIN NG TABULAR
    for (i, (emotion, prob)) in enumerate(zip(EMOTIONS, preds)):
                text = "{}: {:.2f}%".format(emotion, prob * 100)
                w = int(prob * 300)
                cv2.rectangle(canvas, (7, (i * 35) + 5),
                (w, (i * 35) + 35), (0, 0, 255), -1)
                cv2.putText(canvas, text, (10, (i * 35) + 23),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                (255, 255, 255), 2)
                cv2.putText(frameCopy, label, (fX, fY - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
                cv2.rectangle(frameCopy, (fX, fY), (fX + fW, fY + fH),
                              (0, 0, 255), 2)

    cv2.imshow('Actual', frameCopy)
    cv2.imshow("Tabular", canvas)
     
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
camera.release()
cv2.destroyAllWindows()

