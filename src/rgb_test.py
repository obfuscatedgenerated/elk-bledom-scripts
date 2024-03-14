import asyncio
from bledom.device import BleLedDevice
from bleak import BleakScanner, BleakClient

from dotenv import load_dotenv
from os import getenv

load_dotenv()

TARGET_DEVICE = getenv("TARGET_DEVICE")

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

async def main():
    print("Connecting to device...")

    async with BleakClient(TARGET_DEVICE) as client:
        print("Connected to device")
        
        device = await BleLedDevice.new(client)
        await device.power_on()
        
        await device.set_color(255, 0, 0)
        await asyncio.sleep(1)
        await device.set_color(0, 255, 0)
        await asyncio.sleep(1)
        await device.set_color(0, 0, 255)
        await asyncio.sleep(1)
        await device.set_color(0, 0, 0)

asyncio.run(main())
