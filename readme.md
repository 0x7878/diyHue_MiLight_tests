# DiyHue MiLight Tests

This Project used the DIYHue codebase as a minimum subset to send some UDP Commonads to a Milight Bridge v6.
It will change the color of a bulb as fast as you configure. It was usefull to me figure out which paramater fits without overloading the bridge.

## Setup

- clone this repo
- your milight bridge should already have a configured UDP Listener
- adjust the variable addresses in the main.py to your needs. (change the IP and the port)

``` JSON
"9": {
        "group": 1,
        "ip": "192.168.1.224",
        "light_type": "rgbww",
        "port": 5987,
        "protocol": "mi_box"
```

- to start the project enter: ``` python  main.py ```
