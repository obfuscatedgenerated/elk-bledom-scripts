from typing import Tuple

import asyncio

from bledom.device import BleLedDevice
from bleak import BleakScanner, BleakClient

from PIL import Image
from mss import mss
 
from tweener import Tween, Easing, EasingMode

from dotenv import load_dotenv
from os import getenv

load_dotenv()

TARGET_DEVICE = getenv("TARGET_DEVICE")

# the required change in distance between the current color and the target color to trigger an update
CHANGE_THRESHOLD = 10

# the time between each color change in milliseconds. smaller time = less smooth but more responsive
TWEEN_TIME = 500

# the easing curve to use for the color change
TWEEN_EASE = Easing.QUAD

# the easing mode to use for the color change
TWEEN_MODE = EasingMode.IN_OUT

# TODO proper way to disable fading

# the time between each screen capture in milliseconds
UPDATE_RATE = int(1 / 60) * 1000

# the initial color of the LED
INIT_COLOR = (0, 0, 0)

# the resolution of the screen capture. bigger = slower/more intensive but more accurate average color
RESOLUTION = (64, 64)

# the monitor index to capture, starting from 1. -1 for all monitors
MONITOR_INDEX = 1

async def scan_routine():
    print ("Scanning for devices...")
    devices = await BleakScanner.discover()
    for device in devices:
        print(device)
    
    print("Please set TARGET_DEVICE environment variable (or .env) to the address of the device you want to connect to")

if TARGET_DEVICE is None or TARGET_DEVICE == "":
    print("TARGET_DEVICE environment variable is not set")

    print("Scanning for devices...")
    asyncio.run(scan_routine())
    exit(1)

# TODO: move setup to common file
# TODO: make library quiet
    

current_color: Tuple[int, int, int] = INIT_COLOR
target_color: Tuple[int, int, int] = INIT_COLOR

tween_r: Tween | None = None
tween_g: Tween | None = None
tween_b: Tween | None = None
# TODO: avoid flickering from multiple color updates at once (tweens are replaced immediately from current value)
# especially from sudden changes. could also perhaps detect sudden changes and skip tweening optionally

async def color_task(device):
    global current_color
    global target_color

    global tween_r
    global tween_g
    global tween_b

    while True:
        # allow other tasks to run
        await asyncio.sleep(0)

        if tween_r is None or tween_g is None or tween_b is None:
            continue

        if tween_r.animating:
            tween_r.update()
        if tween_g.animating:
            tween_g.update()
        if tween_b.animating:
            tween_b.update()

        current_color = (int(tween_r.value), int(tween_g.value), int(tween_b.value))

        if current_color == target_color:
            continue

        asyncio.create_task(device.set_color(*current_color))

async def screen_task():
    global current_color
    global target_color

    global tween_r
    global tween_g
    global tween_b


    with mss() as sct:
        while True:
            await asyncio.sleep(UPDATE_RATE)

            grab = sct.grab(sct.monitors[MONITOR_INDEX])
            im = Image.frombytes("RGB", grab.size, grab.bgra, "raw", "BGRX")

            im = im.resize(RESOLUTION)
            pixels = list(im.getdata())

            # get the average color of the screen
            r = 0
            g = 0
            b = 0

            for pixel in pixels:
                r += pixel[0]
                g += pixel[1]
                b += pixel[2]

            r = int(r / len(pixels))
            g = int(g / len(pixels))
            b = int(b / len(pixels))

            # if the color hasn't changed enough, don't update the target color
            if abs(r - target_color[0]) <= CHANGE_THRESHOLD and abs(g - target_color[1]) <= CHANGE_THRESHOLD and abs(b - target_color[2]) <= CHANGE_THRESHOLD:
                continue

            target_color = (r, g, b)

            tween_r = Tween(current_color[0], target_color[0], TWEEN_TIME, TWEEN_EASE, TWEEN_MODE)
            tween_g = Tween(current_color[1], target_color[1], TWEEN_TIME, TWEEN_EASE, TWEEN_MODE)
            tween_b = Tween(current_color[2], target_color[2], TWEEN_TIME, TWEEN_EASE, TWEEN_MODE)

            tween_r.start()
            tween_g.start()
            tween_b.start()
            

async def main():
    print("Connecting to device...")

    async with BleakClient(TARGET_DEVICE) as client:
        print("Connected to device")
        
        device = await BleLedDevice.new(client)

        await device.power_on()
        print("Device powered on")

        await device.set_color(*INIT_COLOR)

        # run both loops in parallel
        await asyncio.gather(color_task(device), screen_task())

asyncio.run(main())

# TODO: optionally prefer edges of screen
# TODO: gui for settings
