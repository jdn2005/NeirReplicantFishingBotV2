import numpy as np
import cv2
from mss import mss
import math
import pynput
from pynput.keyboard import Key
import time
import json
import os
from enum import Enum

import Calibration


class State(Enum):
    IDLE = 0
    STOPPED = 1

    #True while the fish health bar is on screen
    #is attempting to kill the fish
    REELING = 2 

    #true between deciding to cast and the bobber having been cast
    #it is waiting for the bobber to appear
    CASTING = 3 

    #true while the bobber is out 
    #it is looking for when the bobber disapears
    BOBBER = 4 

    DEBUG = 5

    RECOVERY = 6


# Load configuration from config.json
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

if not os.path.exists(config_path):
    print("No config.json found. Running calibration...")
    Calibration.run_calibration()

with open(config_path, "r") as f:
    config = json.load(f)

gameResolution = np.array(config["game_resolution"])
screenResolution = np.array(config["screen_resolution"])
baitNumber = config["bait_number"]
numberOfAttempts = config["number_of_attempts"]


attemptCounter = 0
state = State.IDLE
mouse = pynput.mouse.Controller()
keyboard = pynput.keyboard.Controller()


def on_press(key):
    global state, attemptCounter

    try:
        if key.char == "o":
            state = State.STOPPED

        if key.char == "i":
            if state == State.IDLE:
                attemptCounter = 0
                state = State.CASTING
            else:
                state = State.IDLE

    except AttributeError:
        pass

def on_release(key):
    pass

listener = pynput.keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.start()

bounding_box = {'top': int(math.floor((screenResolution[1] - gameResolution[1]) / 2)), 'left': int(math.floor((screenResolution[0] - gameResolution[0]) / 2)) , 'width': int(gameResolution[0]), 'height': int(gameResolution[1])}


sct = mss()


def capture_screen():
    screenshot = sct.grab(bounding_box)
    img = np.array(screenshot)  # This includes alpha channel (RGBA)
    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)  # Remove alpha for OpenCV compatibility
    return img


def pressKey(key):
    keyboard.press(key)
    time.sleep(0.05)
    keyboard.release(key)
    time.sleep(0.05)



#CIELAB
bobberLowerBound = np.array([0, 170, 135])
bobberUpperBound = np.array([255, 255, 255])

colorLowerPercentile = np.array([30, 0, 100])
colorUpperPercentile = np.array([88, 255, 183])


def cast(number = 0):
    global state, attemptCounter

    if attemptCounter >= numberOfAttempts and numberOfAttempts >= 0:
        state = State.IDLE
        return
    elif numberOfAttempts >= 0:
        attemptCounter += 1

    if state != State.CASTING:
        raise RuntimeError("Cast when not in CASTING state")
    
    pressKey('f')
    for i in range(number):
        time.sleep(0.1)
        pressKey(Key.down)


    time.sleep(0.1)
    pressKey(Key.enter)

    if state != State.CASTING:
        return

    state = State.BOBBER



def isBobberOnScreen():

    # Convert BGR image to HLS (Hue, Lightness, Saturation)
    lab_image = cv2.cvtColor(capture_screen(), cv2.COLOR_BGR2Lab)

    return np.any(cv2.inRange(lab_image, bobberLowerBound, bobberUpperBound))

def bobber():
    global state
    if state != State.BOBBER:
        raise RuntimeError("Bobber when not in BOBBER state")

    bobberCounter = 0
    while bobberCounter < 10 and state == State.BOBBER:
        bobberCounter += isBobberOnScreen()

    while isBobberOnScreen() and state == State.BOBBER:
        pass
    
    if state != State.BOBBER:
        return

    pressKey(Key.enter)
    state = State.REELING


fishHealthBarLower = np.array([0, 120, 0])
fishHealthBarUpper = np.array([255, 171, 128])

def fishHealthPercent():

    # Convert BGR image to HLS (Hue, Lightness, Saturation)
    image = capture_screen()

    #pixel offsets that change with screen resolution
    temp = np.floor(image.shape[0] * 0.405)
    temp1 = int(30 / 1440.0 * gameResolution[1])
    temp2 = int(20 / 1440.0 * gameResolution[1])
    temp3 = int(10 / 1440.0 * gameResolution[1])
    #if there is a black bar on the screen then the fish is definitely gone
    A = np.mean(image[int(temp - temp1) : int(temp - temp2), :])#Above the Bar
    B = np.mean(image[int(temp + temp2) : int(temp + temp1), :])#Below the Bar
         
    if np.mean(image[int(temp - temp3) : int(temp + temp3), :]) < 10 or A  / B > 2:
        return -1

    #pixel offsets that change with screen resolution
    lV = int(1340 / 1440.0 * gameResolution[1])
    uV = int(-75 / 1440.0 * gameResolution[1])

    lH = int(775 / 2560.0 * gameResolution[0])
    uH = int(-820 / 2560.0 * gameResolution[0])
    pullBar = image[lV : uV, lH : uH]
    lab_image = cv2.cvtColor(pullBar, cv2.COLOR_BGR2Lab)

    pullBar = cv2.inRange(lab_image, fishHealthBarLower, fishHealthBarUpper)

    return np.mean(pullBar)

def reeling():
    global state

    if state != State.REELING:
        raise RuntimeError("Reeling when not in REELING state")
    
    while state == State.REELING:
        temp = fishHealthPercent()
        if temp > 100 or temp < 0:
            break
        pass

    fishHealth = fishHealthPercent()

    lastTime = time.perf_counter()
    keyboard.press("s")
    pullDirection = 0

    while state == State.REELING and fishHealth >= 0:
        newFishHealth = fishHealthPercent()

        #print(fishHealth, newFishHealth)
        if fishHealth < 0:
            break

        if newFishHealth >= fishHealth:
            now = time.perf_counter()
            if now - lastTime > 0.1:
                pullDirection += 1
                pullDirection = pullDirection % 3
                lastTime = now

                if pullDirection == 0:
                    keyboard.release("a")
                    keyboard.release("d")
                elif pullDirection == 1:
                    keyboard.press("a")
                    keyboard.release("d")
                elif pullDirection == 2:
                    keyboard.press("d")
                    keyboard.release("a")

        if newFishHealth < fishHealth:
            fishHealth = newFishHealth

    keyboard.release("s")
    keyboard.release("a")
    keyboard.release("d")

    if state != State.REELING:
        return 
    
    state = State.RECOVERY

def recovery():
    global state

    if state != State.RECOVERY:
        raise RuntimeError("Recovery when not in RECOVERY state")

    time.sleep(0.5)
    pressKey(Key.enter)
    time.sleep(0.5)
    pressKey(Key.enter)

    state = State.CASTING

print("Press i to toggle bot activation.")
print("Press o to stop program.")

while state != State.STOPPED:
    if state == State.DEBUG:
        state = State.CASTING

    if state == State.CASTING:
        if numberOfAttempts >= 0:
            if attemptCounter < numberOfAttempts:
                print("Casting " + str(attemptCounter + 1) + " / " + str(numberOfAttempts))
        else:
            print("Casting")
        
        cast(baitNumber)

    if state == State.BOBBER:
        print("Bobber")
        bobber()
    
    if state == State.REELING:
        print("Reeling")
        reeling()

    if state == State.RECOVERY:
        print("Recovery")
        recovery()
        print()

