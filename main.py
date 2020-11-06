import json
import logging
import sys
from time import sleep, strftime
import protocols
from functions.lightRequest import sendLightRequest
from functions.colors import convert_rgb_xy, convert_xy

root = logging.getLogger()
root.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

addresses = {
    "9": {
        "group": 1,
        "ip": "192.168.1.224",
        "light_type": "rgbww",
        "port": 5987,
        "protocol": "mi_box"
    }
}
lightsjson = """{
    "9": {
        "capabilities": {
            "certified": true,
            "control": {
                "colorgamut": [
                    [
                        0.6915,
                        0.3083
                    ],
                    [
                        0.17,
                        0.7
                    ],
                    [
                        0.1532,
                        0.0475
                    ]
                ],
                "colorgamuttype": "C",
                "ct": {
                    "max": 500,
                    "min": 153
                },
                "maxlumen": 800,
                "mindimlevel": 1000
            },
            "streaming": {
                "proxy": true,
                "renderer": true
            }
        },
        "config": {
            "archetype": "sultanbulb",
            "direction": "omnidirectional",
            "function": "mixed",
            "startup": {
                "configured": false,
                "mode": "safety"
            }
        },
        "manufacturername": "Philips",
        "modelid": "LCT015",
        "name": "MiLight rgb_cct 0x1",
        "productname": "Hue color lamp",
        "state": {
            "alert": "none",
            "bri": 85,
            "colormode": "ct",
            "ct": 162,
            "effect": "none",
            "hue": 10280,
            "mode": "homeautomation",
            "on": true,
            "reachable": true,
            "sat": 250,
            "transitiontime": 0,
            "xy": [
                0.256412,
                0.673179
            ]
        },
        "swversion": "1.46.13_r26312",
        "type": "Extended color light",
        "uniqueid": "1a2b3c447"
    }
}
"""

lights  = json.loads(lightsjson)

lights["9"]["state"].update({"on": True, "bri": int((255 + 0 + 0) / 3), "xy": convert_rgb_xy(255, 0, 0), "colormode": "xy"})

def setColor(data, sleepTime):
    r, g, b = data
    sendLightRequest("9",  {"xy": lights["9"]["state"]["xy"]}, lights, addresses, [r, g, b])
    sleep(sleepTime)

for i in range(1, 20):
    setColor([255, 0, 0], 0.05)
    setColor([0, 255, 0], 0.05)
