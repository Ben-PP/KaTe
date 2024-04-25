# KaTe

KaTe is a DIY temperature sensor for Home Assistant. It uses Raspberry pi Pico W and bme680 for hardware and MQTT for communication.

## Set up

Coming soon... You'll need to wire the bme680 to the pico and flash the pico with micropython firmware. Next copy the `config.example.py` to `config.py` and modify the values as needed. Finally upload `main.py`, `mqtt.py`, `bme680.py` and the `config.py` to the Pico.

## bme680 library

The library bme680.py is this [BME680-Micropython](https://github.com/robert-hh/BME680-Micropython) with minor modifications. It is licensed with MIT license and it is found in the file.

## MQTT library

The library mqtt.py is umqtt.simple from [micropython-lib](https://github.com/micropython/micropython-lib) and is under their licensing.
