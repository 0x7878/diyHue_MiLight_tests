import logging, json
from functions.request import sendRequest
from functions.colors import convert_rgb_xy, convert_xy, rgbBrightness 
from subprocess import check_output
from protocols import protocols
from datetime import datetime, timedelta
from time import sleep
from functions.updateGroup import updateGroupStats

protoList = {}

def getProtocol(protocol_name):
    if(len(protoList) == 0 ):
         for protocol in protocols:
             protoList[protocol.__name__] = protocol

    return protoList["protocols." + protocol_name]
               

def sendLightRequest(light, data, lights, addresses, rgb = None, entertainmentHostIP = None):
    payload = {}
    if light in addresses:
        protocol_name = addresses[light]["protocol"]

        protocol = getProtocol(protocol_name)

        try:
            if protocol_name in ["yeelight", "mi_box", "esphome", "tasmota"]:
                protocol.set_light(addresses[light], lights[light], data, rgb)
            else:
                protocol.set_light(addresses[light], lights[light], data)
        except Exception as e:
            lights[light]["state"]["reachable"] = False
            logging.warning(lights[light]["name"] + " light not reachable: %s", e)
        return

def syncWithLights(lights, addresses, users, groups, off_if_unreachable): #update Hue Bridge lights states
    while True:
        logging.info("sync with lights")
        for light in addresses:
            try:
                protocol_name = addresses[light]["protocol"]
                for protocol in protocols:
                    if "protocols." + protocol_name == protocol.__name__:
                        try:
                            light_state = protocol.get_light_state(addresses[light], lights[light])
                            lights[light]["state"].update(light_state)
                            lights[light]["state"]["reachable"] = True
                        except Exception as e:
                            lights[light]["state"]["reachable"] = False
                            lights[light]["state"]["on"] = False
                            logging.warning(lights[light]["name"] + " is unreachable: %s", e)

                if addresses[light]["protocol"] == "native":
                    light_data = json.loads(sendRequest("http://" + addresses[light]["ip"] + "/get?light=" + str(addresses[light]["light_nr"]), "GET", "{}"))
                    lights[light]["state"].update(light_data)
                    lights[light]["state"]["reachable"] = True
                elif addresses[light]["protocol"] == "hue":
                    light_data = json.loads(sendRequest("http://" + addresses[light]["ip"] + "/api/" + addresses[light]["username"] + "/lights/" + addresses[light]["light_id"], "GET", "{}"))
                    lights[light]["state"].update(light_data["state"])
                elif addresses[light]["protocol"] == "ikea_tradfri":
                    light_data = json.loads(check_output("./coap-client-linux -m get -u \"" + addresses[light]["identity"] + "\" -k \"" + addresses[light]["preshared_key"] + "\" \"coaps://" + addresses[light]["ip"] + ":5684/15001/" + str(addresses[light]["device_id"]) +"\"", shell=True).decode('utf-8').rstrip('\n').split("\n")[-1])
                    lights[light]["state"]["on"] = bool(light_data["3311"][0]["5850"])
                    lights[light]["state"]["bri"] = light_data["3311"][0]["5851"]
                    if "5706" in light_data["3311"][0]:
                        if light_data["3311"][0]["5706"] == "f5faf6":
                            lights[light]["state"]["ct"] = 170
                        elif light_data["3311"][0]["5706"] == "f1e0b5":
                            lights[light]["state"]["ct"] = 320
                        elif light_data["3311"][0]["5706"] == "efd275":
                            lights[light]["state"]["ct"] = 470
                    else:
                        lights[light]["state"]["ct"] = 470
                    lights[light]["state"]["reachable"] = True
                elif addresses[light]["protocol"] == "milight":
                    light_data = json.loads(sendRequest("http://" + addresses[light]["ip"] + "/gateways/" + addresses[light]["device_id"] + "/" + addresses[light]["mode"] + "/" + str(addresses[light]["group"]), "GET", "{}"))
                    if light_data["state"] == "ON":
                        lights[light]["state"]["on"] = True
                    else:
                        lights[light]["state"]["on"] = False
                    if "brightness" in light_data:
                        lights[light]["state"]["bri"] = light_data["brightness"]
                    if "color_temp" in light_data:
                        lights[light]["state"]["colormode"] = "ct"
                        lights[light]["state"]["ct"] = int(light_data["color_temp"] * 1.6)
                    elif "bulb_mode" in light_data and light_data["bulb_mode"] == "color":
                        lights[light]["state"]["colormode"] = "hs"
                        lights[light]["state"]["hue"] = light_data["hue"] * 180
                        if (not "saturation" in light_data) and addresses[light]["mode"] == "rgbw":
                            lights[light]["state"]["sat"] = 255
                        else:
                            lights[light]["state"]["sat"] = int(light_data["saturation"] * 2.54)
                    lights[light]["state"]["reachable"] = True
                elif addresses[light]["protocol"] == "domoticz": #domoticz protocol
                    light_data = json.loads(sendRequest("http://" + addresses[light]["ip"] + "/json.htm?type=devices&rid=" + addresses[light]["light_id"], "GET", "{}"))
                    if light_data["result"][0]["Status"] == "Off":
                         lights[light]["state"]["on"] = False
                    else:
                         lights[light]["state"]["on"] = True
                    lights[light]["state"]["bri"] = str(round(float(light_data["result"][0]["Level"])/100*255))
                    lights[light]["state"]["reachable"] = True
                elif addresses[light]["protocol"] == "jeedom": #jeedom protocol
                    light_data = json.loads(sendRequest("http://" + addresses[light]["ip"] + "/core/api/jeeApi.php?apikey=" + addresses[light]["light_api"] + "&type=cmd&id=" + addresses[light]["light_id"], "GET", "{}"))
                    if light_data == 0:
                         lights[light]["state"]["on"] = False
                    else:
                         lights[light]["state"]["on"] = True
                    lights[light]["state"]["bri"] = str(round(float(light_data)/100*255))
                    lights[light]["state"]["reachable"] = True

                if off_if_unreachable:
                    if lights[light]["state"]["reachable"] == False:
                        lights[light]["state"]["on"] = False
                updateGroupStats(light, lights, groups)
                sleep(0.5)
            except Exception as e:
                lights[light]["state"]["reachable"] = False
                lights[light]["state"]["on"] = False
                logging.warning(lights[light]["name"] + " is unreachable: %s", e)
        sleep(10) #wait at last 10 seconds before next sync
        i = 0
        while i < 300: #sync with lights every 300 seconds or instant if one user is connected
            for user in users.keys():
                lu = users[user]["last use date"]
                try: #in case if last use is not a proper datetime
                    lu = datetime.strptime(lu, "%Y-%m-%dT%H:%M:%S")
                    if abs(datetime.now() - lu) <= timedelta(seconds = 2):
                        i = 300
                        break
                except:
                    pass
            i += 1
            sleep(1)
