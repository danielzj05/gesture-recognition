import math
import cv2 as cv
import mediapipe as mp
import serial
import time
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
expected_max = []

calibrated = False  # Flag to check if calibration is done
# attempt to open the serial port; if it fails, we will just not send any data
try:
    arduino = serial.Serial('COM3', 250000, timeout=0.05)
    time.sleep(2)
except serial.SerialException as e:
    print(f"Could not open serial port: {e}")
    arduino = None

cap = cv.VideoCapture(0) # open the default camera

# hold every finger's landmarks
@dataclass
class finger:
    mcp: any
    pip: any
    dip: any
    tip: any

@dataclass
class max_expected:
    x: float
    y: float
    
def calibrate_hand(hand_landmarks):
    # find the maximum expected distance for normalization (essentially the "length" of the finger)

    # manually add thumb
    thumb = max_expected(
        x=hand_landmarks.landmark[4].x - hand_landmarks.landmark[2].x,
        y=hand_landmarks.landmark[4].y - hand_landmarks.landmark[2].y
    )
    expected_max.append(thumb)
    # Iterate through each landmark; we only need 5 to 20 for fingers and every 4th landmark corresponds to a finger
    for i in range(5, 21, 4):
        digit = max_expected(
            x=hand_landmarks.landmark[i + 3].x - hand_landmarks.landmark[i].x,
            y=hand_landmarks.landmark[i + 3].y - hand_landmarks.landmark[i].y
        )
        expected_max.append(digit)
    return

# probably should rename this to helper lol
def straightness(finger, idx):
    # attempt 2 we are gonna find the difference btwn the tip and the knuckle
    # (tip and MCP)
    # the decimals are too long so we are gonna clamp it to like 5 decimal places

    # note the normalized values are between 0 and 1 AND starts from the tip (tip is always closer to 0)
    dy = round(finger.mcp.y - finger.tip.y, 5)
    dx = round(finger.mcp.x - finger.tip.x, 5)
    max_val = expected_max[idx]

    # if the x distance is greater than the y distance, the hand is rotated more horizontally, 
    # so we normalize by x, otherwise by y
    if dx >= max_val.x:
        normalized = dx / max_val.y
        clamped = max(0, min(normalized, 1))
    else:
        normalized = dy / max_val.y
        clamped = max(0, min(normalized, 1))
    return clamped

# find the straightness of all fingers
def detect_finger_straightness(hand_landmarks):
    # define a threshold for straightness; normalized coordinates are between 0 and 1 - scale to 255 for LED
    # apparently you find the average y-coordinate of the longest part of the palm and.. compare it to the y-coordinate of the finger tips
    
    # unfortunately the mediapipe hands tracks thumbs differently so we are manually adding it
    # im also not gonna add another object just for the thumb so i will comment its actual name next to it
    thumb = finger(
        mcp=hand_landmarks.landmark[2], # cmc
        pip=hand_landmarks.landmark[3], # mcp
        # we are gonna reuse this value (basically make it the same point) because the thumb only has 2 segments
        dip=hand_landmarks.landmark[3], # ip
        tip=hand_landmarks.landmark[4]  # tip
    )
    fingers.append(thumb)  # add the thumb to the fingers list

    # Iterate through each landmark; we only need 5 to 20 for fingers and every 4th landmark corresponds to a finger
    for i in range(5, 21, 4):
        finger_obj = finger(
            mcp=hand_landmarks.landmark[i],
            pip=hand_landmarks.landmark[i + 1],
            dip=hand_landmarks.landmark[i + 2],
            tip=hand_landmarks.landmark[i + 3]
        )
        fingers.append(finger_obj)

    for idx, digit in enumerate(fingers):
        scale = int(straightness(digit, idx)*255) # Scale to 0-255 for LED
        finger_straightness.append(scale)

    return

# debug
#frame_count = 0

# main loop to capture video and process hand landmarks
try:
    while True:
        #if frame_count >= 1: 
            #break

        ret, frame = cap.read() # ret = true if frame is read correctly
        frame = cv.flip(frame, 1)  # Flip the frame horizontally for a mirror effect
        # frame is some media pipe object

        res = hand_object.process(cv.cvtColor(frame, cv.COLOR_BGR2RGB))  # Process the frame for hand detection; reads in BGR for some reason
        
        # because of the scarce documentation (at least for python), I'm gonna leave this as a note:
        # res.multi_hand_landmarks is a list of detected hands, each containing landmarks
        # res.multi_hand_world_landmarks is a list of detected hands, each containing world landmarks
        # res.multi_hand_landmarks contains the landmarks of the detected hands in the frame, and are 3D world coordinates
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

                if not calibrated:  # if we haven't calibrated yet
                    calibrate_hand(hand_landmarks)  # calibrate the hand landmarks
                    calibrated = True

                detect_finger_straightness(hand_landmarks)
                
                # just a safety thing in case we didnt get 5 fingers in the last frame
                if arduino and len(finger_straightness) == 5:
                    arduino.write(bytes(finger_straightness))

                # Print the straightness values for debugging
                '''for i, straightness in enumerate(finger_straightness):
                    if i == 0:
                        print(f"Thumb straightness: {straightness:.2f}")
                    elif i == 1:
                        print(f"Index finger straightness: {straightness:.2f}")
                    elif i == 2:
                        print(f"Middle finger straightness: {straightness:.2f}")
                    elif i == 3:
                        print(f"Ring finger straightness: {straightness:.2f}")
                    elif i == 4:
                        print(f"Little finger straightness: {straightness:.2f}")'''
                

        cv.imshow('Camera Feed', frame)

        if cv.waitKey(10) & 0xFF == ord('r'):
            expected_max.clear()
            calibrated = False

        # Check for key presses and mask key (ord()'q') to quit
        if cv.waitKey(10) & 0xFF == ord('q'):
            break
        #frame_count += 1
finally:
    cap.release()
    cv.destroyAllWindows()