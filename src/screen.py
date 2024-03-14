import asyncio

from bledom.device import BleLedDevice
from bleak import BleakScanner, BleakClient

from PIL import ImageGrab

from dotenv import load_dotenv
from os import getenv

load_dotenv()

TARGET_DEVICE = getenv("TARGET_DEVICE")

# the number of steps to take to get to the new color. more = smoother but slower
CHANGE_STEPS = 50

# the time for each step in the color change
CHANGE_RATE = 0.005

# the time between each screen capture
UPDATE_RATE = 0.1

# the initial color of the LED
INIT_COLOR = (0, 0, 0)

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

        # get the distance between the current color and the target color
        dr = target_color[0] - current_color[0]
        dg = target_color[1] - current_color[1]
        db = target_color[2] - current_color[2]

        # if the distance is 0, we're done
        if dr == 0 and dg == 0 and db == 0:
            continue

        # interpolate the color
        current_color = (int(current_color[0] + dr / CHANGE_STEPS), int(current_color[1] + dg / CHANGE_STEPS), int(current_color[2] + db / CHANGE_STEPS))

        await device.set_color(*current_color) # TODO run without awaiting, means we can just skip a step if there is latency

async def screen_task():
    global target_color

    while True:
        im = ImageGrab.grab()

        im = im.resize((16, 16))
        im = im.convert("RGB")

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