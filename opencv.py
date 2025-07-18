import math
import cv2 as cv
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from dataclasses import dataclass

# Initialize MediaPipe Hands
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hand_object = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)

fingers = []  # holds finger length values
finger_straightness = []  # holds finger straightness values

cap = cv.VideoCapture(0) # open the default camera

# hold every finger's landmarks
@dataclass
class finger:
    mcp: any
    pip: any
    dip: any
    tip: any


def distance(point1, point2):
    # distance between 2 points (for finger straightness); we dotn need z cuz its depth and we're only working in 2D
    return math.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)

def straightness_ratio(finger):
    # Calculate the lengths of the finger segments
    mcp_to_pip = distance(finger.mcp, finger.pip)
    pip_to_dip = distance(finger.pip, finger.dip)
    dip_to_tip = distance(finger.dip, finger.tip)

    # Calculate the total length of the finger
    total_length = mcp_to_pip + pip_to_dip + dip_to_tip
    actual_length = distance(finger.mcp, finger.tip)

    ''' ngl logic is kinda weird; but if you imagine a straight line from the tip of your finger to
        your first knuckle, then imagine like, you bent your fingers, you introduce a curve where if you 
        sum of the segments its technically longer than the straight line distance (i think anyways)
    ''' 
    return actual_length / total_length

# find the straightness of all fingers
def detect_finger_straightness(hand_landmarks):
    # define a threshold for straightness; normalized coordinates are between 0 and 1 - scale to 255 for LED
    # apparently you find the average y-coordinate of the longest part of the palm and.. compare it to the y-coordinate of the finger tips
    
    # Iterate through each landmark; we only need 5 to 20 for fingers and every 4th landmark corresponds to a finger
    for i in range(5, 21, 4):
        finger_obj = finger(
            mcp=hand_landmarks.landmark[i],
            pip=hand_landmarks.landmark[i + 1],
            dip=hand_landmarks.landmark[i + 2],
            tip=hand_landmarks.landmark[i + 3]
        )
        fingers.append(finger_obj)

    for digit in fingers:
        straightness = straightness_ratio(digit)*255 # Scale to 0-255 for LED
        finger_straightness.append(straightness)

    return

while True:
    ret, frame = cap.read() # ret = true if frame is read correctly
    frame = cv.flip(frame, 1)  # Flip the frame horizontally for a mirror effect
    # frame is some media pipe object

    res = hand_object.process(cv.cvtColor(frame, cv.COLOR_BGR2RGB))  # Process the frame for hand detection; reads in BGR for some reason
    
    # because of the scarce documentation (at least for python), I'm gonna leave this as a note:
    # res.multi_hand_landmarks is a list of detected hands, each containing landmarks
    # res.multi_hand_world_landmarks is a list of detected hands, each containing world landmarks
    #res.multi_hand_landmarks contains the landmarks of the detected hands in the frame, and are 3D world coordinates
    # - this is not normalized for 2d image rendering and can look really weird if you try to draw them directly
    # hand_landmarks is a list of landmarks for each detected hand and is normalized for 2D image rendering

    if res.multi_hand_landmarks: # detects a list of hands in the frame
        fingers.clear()  # clear the previous finger data
        finger_straightness.clear()  # clear the previous straightness data

        for hand_landmarks in res.multi_hand_landmarks:
            # draw the hand landmarks and connections
            mp_drawing.draw_landmarks(
                frame, 
                #res.multi_hand_world_landmarks[0], # this draws keypoints in the hand ngl idk why it draws it in some corner
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS, 
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            detect_finger_straightness(hand_landmarks)
            # Print the straightness values for debugging
            for i, straightness in enumerate(finger_straightness):
                print(f"Finger {i + 1} straightness: {straightness:.2f}")

    cv.imshow('Camera Feed', frame)

    # Check for key presses and mask key (ord()'q') to quit
    if cv.waitKey(1) & 0xFF == ord('q'):
        cap.release()
        cv.destroyAllWindows()
        break