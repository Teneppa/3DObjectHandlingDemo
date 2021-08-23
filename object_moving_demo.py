"""This demo is made by Teukkaniikka

This is a work in progress!
"""

import math
import os
import cv2
import mediapipe as mp
import numpy as np

from numpy.linalg.linalg import norm
from graphicsEngine import graphicsEngine
from numpy import linalg as LA

g = graphicsEngine()

g.translateMatrix(0, 0, 0)
g.updateProjectionMatrix()

g.drawOnlyPoints = 1
g.pointRadius = 1
g.pointThickness = 1
g.zoomStep = 10
g.movingSpeed = 1
g.enableMouse = 0
g.debugTranslation = 1

# ///////////////////////////////////
# // Add point to the point matrix //
# ///////////////////////////////////
def pointMatrixAdd(x, y, z):
    pointString = ''
    pointString += str(x)
    pointString += ','
    pointString += str(y)
    pointString += ','
    pointString += str(z)
    pointString += ',1'

    g.pointMatrix = np.append(g.pointMatrix, np.matrix(pointString), 0)


def loadMatrixFromFile(filename):
    if not os.path.isfile(filename):
        print("No file named "+filename)
        return

    g.pointMatrix = np.zeros((4, 4))

    with open(filename) as data:
        for line in data:
            point = line.split(" ", 3)
            pointMatrixAdd(float(point[0]), float(point[1]), float(point[2]))


loadMatrixFromFile("monk.txt")

# Hand tracking stuff
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands
drawing_styles = mp.solutions.drawing_styles

# For webcam input:
cap = cv2.VideoCapture(1)

# Put the camera resolution and scaling factor here
# Just set it to 1 if you don't want to up-/downscale it
camera_width = 1280
camera_height = 720
scale = 1

img_width = int(camera_width*scale)
img_height = int(camera_height*scale)

# NOTE: http://geom3d.com/data/documents/Calculation=20of=20Euler=20angles.pdf
def lcs2Euler(X1x, X1y, X1z, Y1x, Y1y, Y1z, Z1x, Z1y, Z1z):
    Z1xy = math.sqrt(Z1x ** 2 + Z1y ** 2)

    if Z1xy > np.finfo(float).eps:
        pre = math.atan2(Y1x * Z1y - Y1y*Z1x, X1x * Z1y - X1y * Z1x)
        nut = math.atan2(Z1xy, Z1z)
        rot = -math.atan2(-Z1x, Z1y)
    else:
        pre = 0.0
        # nut = (Z1z > 0.) ? 0 : math.pi;
        nut = 0 if Z1z > 0 else math.pi
        rot = -math.atan2(X1y, X1x)

    return pre, nut, rot


def normal(a, b, c):
    return np.cross(np.add(a, b), np.add(b, c))


def distance(a, b):
    return math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2 + (a.z-b.z)**2)


# Detect the start of pinch
pinching = False

# The absolute location of the 3d-object
location = [0, 0, 0]

# The absolute location of the hand when the pinch starts
startlocation = [0, 0, 0]

change = [0, 0, 0]

with mp_hands.Hands(
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as hands:
    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue

        # Flip the image horizontally for a later selfie-view display, and convert
        # the BGR image to RGB.
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (img_width, img_height))

        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        image.flags.writeable = False
        results = hands.process(image)

        # Draw the hand annotations on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    drawing_styles.get_default_hand_landmark_style(),
                    drawing_styles.get_default_hand_connection_style())

                # Find the markers for the index finger and thumb, calculate the distance,
                # convert it to brightness and sent it to the Arduino
                try:
                    listOfMarks = hand_landmarks.landmark

                    # breakpoint()

                    # NOTE: https://google.github.io/mediapipe/solutions/hands#python-solution-api

                    #p1 = WRIST
                    #p2 = INDEX_FINGER_MCP
                    #p3 = PINKY_MCP
                    p1 = listOfMarks[0]
                    p2 = listOfMarks[5]
                    p3 = listOfMarks[17]

                    # Fingertips
                    tips = [listOfMarks[4], listOfMarks[8],
                            listOfMarks[12], listOfMarks[16], listOfMarks[20]]
                    dist = []
                    avg = 0
                    for i in range(0, 4):
                        avg += distance(tips[i], tips[i+1])
                        dist.append(distance(tips[i], tips[i+1]))
                    #print(dist, avg/4)

                    if avg/4 < 0.05:
                        if not pinching:
                            startlocation = listOfMarks[12]
                            pinching = True
                        else:
                            moveScale = 100
                            change = [(startlocation.x - listOfMarks[12].x)*moveScale, (startlocation.y -
                                                                                        listOfMarks[12].y)*moveScale, (startlocation.z - listOfMarks[12].z)*moveScale]

                        #print("PINCH", change)

                        a = [p1.x, p1.y, p1.z]
                        b = [p2.x, p2.y, p2.z]
                        c = [p3.x, p3.y, p3.z]

                        pre, nut, rot = lcs2Euler(
                            p1.x, p1.y, p1.z, p2.x, p2.y, p2.z, p3.x, p3.y, p3.z)

                        #print(math.degrees(pre), math.degrees(nut), math.degrees(rot))

                        # breakpoint()
                        #print(math.degrees(angle), math.degrees(angle2), math.degrees(angle3))

                        g.xAngle = nut
                        g.yAngle = rot
                        g.zAngle = pre+math.pi

                        g.currentX = location[0] + change[0]
                        g.currentY = location[1] + change[1]
                        g.currentZ = location[2] + change[2]

                        print(g.currentX, g.currentY, g.currentZ)
                    else:
                        if pinching:
                            location[0] += change[0]
                            location[1] += change[1]
                            location[2] += change[2]

                        pinching = False

                    g.run()
                    if not g.running:
                        print("GEngine is not running!")
                        break

                # If the markers weren't found (this is probably not needed idk)
                except Exception as e:
                    print(e)

        # Show the image
        cv2.imshow('KeyboardDemo', image)

        # Press <Q> to exit
        if cv2.waitKey(1) & 0xFF == 113 or not g.running:
            break

# Let the camera be free!
cap.release()
