import asyncio

from bledom.device import BleLedDevice
from bleak import BleakScanner, BleakClient

from PIL import Image
from mss import mss

from dotenv import load_dotenv
from os import getenv

load_dotenv()

TARGET_DEVICE = getenv("TARGET_DEVICE")

# the required change in distance between the current color and the target color to trigger an update
CHANGE_THRESHOLD = 5

# the number of steps to take to get to the new color. more = smoother but slower. not much advantage to going over 255 TODO smoothing curves
CHANGE_STEPS = 125

# the time for each step in the color change
CHANGE_RATE = 0.00001

# TODO proper way to disable fading

# the time between each screen capture
UPDATE_RATE = 0.0015

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
    
current_color = INIT_COLOR
target_color = INIT_COLOR

async def color_task(device):
    global current_color
    global target_color

    while True:
        await asyncio.sleep(CHANGE_RATE)

        # get the delta between the current color and the target color
        dr = target_color[0] - current_color[0]
        dg = target_color[1] - current_color[1]
        db = target_color[2] - current_color[2]

        # interpolate the color
        new_r = current_color[0] + dr / CHANGE_STEPS
        new_g = current_color[1] + dg / CHANGE_STEPS
        new_b = current_color[2] + db / CHANGE_STEPS

        current_color = (new_r, new_g, new_b)
        rounded_color = (int(new_r), int(new_g), int(new_b))

        # TODO: implement threshold. distance calc is weird

        asyncio.create_task(device.set_color(*rounded_color)) # run as task (without awaiting), means we can just skip a step if there is latency

async def screen_task():
    global target_color

    while True:
        with mss() as sct:
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

            target_color = (r, g, b)

            await asyncio.sleep(UPDATE_RATE)

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
