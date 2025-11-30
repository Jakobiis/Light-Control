# bulb.py
from kasa import Discover
from kasa.iot import IotBulb


async def discover():
    bulbs = await Discover.discover()
    print(f"Found {len(bulbs)} bulbs")
    if not bulbs:
        raise Exception("No bulbs found")
    return list(bulbs.values())[0].host


async def discover_bulb():
    try:
        ip = await discover()
        print(f"Connected to bulb at {ip}")
        bulb = IotBulb(ip)
        await bulb.update()
        await bulb.turn_on()
        return bulb
    except Exception as e:
        print(f"Discovery failed: {e}")
        return None
