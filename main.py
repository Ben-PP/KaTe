import network
import machine
import json
from bme680 import *
from machine import I2C, Pin
from time import sleep_ms
from mqtt import *
from config import *

SW_VERSION = "2.5.0"
HW_VERSION = "1.0"
DEVICE_NAME = "KaTe Sensor"
MANUFACTURER = "Karel Parkkola"
MODEL = "KaTe"
TEMP_ID = f"{UID}_temp"  # UID is defined in config.py
HUMIDITY_ID = f"{UID}_humidity"
PRESSURE_ID = f"{UID}_pressure"
GAS_ID = f"{UID}_gas"
TEMP_STATE = f"state/{TEMP_ID}"
HUMIDITY_STATE = f"state/{HUMIDITY_ID}"
PRESSURE_STATE = f"state/{PRESSURE_ID}"
GAS_STATE = f"state/{GAS_ID}"
AVAILABILITY_TOPIC = (
    f"homeassistant/availability/{IDENTIFIERS}"  # IDENTIFIERS is defined in config.py
)


def get_discovery_topic(uid: str):
    return f"homeassistant/sensor/{uid}/config"


def discover_temp_sensor(client: MQTTClient, device_data):
    discovery_data = {
        "name": "Temperature Sensor",
        "device_class": "temperature",
        "unique_id": TEMP_ID,
        "state_topic": f"{TEMP_STATE}/value",
        "unit_of_measurement": "C",
        "availability": {
            "topic": AVAILABILITY_TOPIC,
            "payload_available": "online",
            "payload_not_available": "offline",
        },
        "device": device_data,
        "value_template": "{{ value | round(1) }}",
    }
    client.publish(get_discovery_topic(TEMP_ID), json.dumps(discovery_data), False)


def discover_humidity_sensor(client: MQTTClient, device_data):
    discovery_data = {
        "name": "Humidity Sensor",
        "device_class": "humidity",
        "unique_id": HUMIDITY_ID,
        "state_topic": f"{HUMIDITY_STATE}/value",
        "unit_of_measurement": "%",
        "availability": {
            "topic": AVAILABILITY_TOPIC,
            "payload_available": "online",
            "payload_not_available": "offline",
        },
        "device": device_data,
        "value_template": "{{ value | round(0) }}",
    }
    client.publish(get_discovery_topic(HUMIDITY_ID), json.dumps(discovery_data), False)


def discover_pressure_sensor(client: MQTTClient, device_data):
    discovery_data = {
        "name": "Pressure Sensor",
        "device_class": "atmospheric_pressure",
        "unique_id": PRESSURE_ID,
        "state_topic": f"{PRESSURE_STATE}/value",
        "unit_of_measurement": "hPa",
        "availability": {
            "topic": AVAILABILITY_TOPIC,
            "payload_available": "online",
            "payload_not_available": "offline",
        },
        "device": device_data,
        "value_template": "{{ value | round(2) }}",
    }
    client.publish(get_discovery_topic(PRESSURE_ID), json.dumps(discovery_data), False)


def discover_gas_sensor(client: MQTTClient, device_data):
    discovery_data = {
        "name": "Gas Sensor",
        "device_class": "aqi",
        "unique_id": GAS_ID,
        "state_topic": f"{GAS_STATE}/value",
        "availability": {
            "topic": AVAILABILITY_TOPIC,
            "payload_available": "online",
            "payload_not_available": "offline",
        },
        "device": device_data,
        "value_template": "{{ value | round(1) }}",
    }
    client.publish(get_discovery_topic(GAS_ID), json.dumps(discovery_data), False)


def discover(client: MQTTClient):
    device_data = {
        "name": DEVICE_NAME,
        "identifiers": IDENTIFIERS,
    }
    device_data_first = {
        "name": DEVICE_NAME,
        "identifiers": IDENTIFIERS,
        "manufacturer": MANUFACTURER,
        "model": MODEL,
        "sw_version": SW_VERSION,
        "hw_version": HW_VERSION,
    }
    discover_temp_sensor(client, device_data_first)
    discover_humidity_sensor(client, device_data)
    discover_pressure_sensor(client, device_data)
    discover_gas_sensor(client, device_data)


def mqtt_connect():
    client = MQTTClient(
        UID,
        MQTT_BROKER,
        keepalive=INTERVAL * 2,
        port=MQTT_PORT,
        user=MQTT_USER,
        password=MQTT_PASSWORD,
    )
    client.set_last_will(AVAILABILITY_TOPIC, "offline", True)
    client.connect(clean_session=False)
    print(f"Connected to {MQTT_BROKER} MQTT Broker")
    discover(client)
    client.publish(AVAILABILITY_TOPIC, "online", True)
    return client


def publish_temp(client: MQTTClient, temp):
    client.publish(f"{TEMP_STATE}/value", temp, True)


def publish_humidity(client: MQTTClient, hum):
    client.publish(f"{HUMIDITY_STATE}/value", str(hum), True)


def publish_pressure(client: MQTTClient, pres):
    client.publish(f"{PRESSURE_STATE}/value", str(pres), True)


def publish_gas(client: MQTTClient, gas):
    client.publish(f"{GAS_STATE}/value", str(gas), True)


def main():
    try:
        i2c = I2C(
            id=1, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN)
        )  # This depends on what pins you are using
        bme = BME680_I2C(i2c=i2c, address=0x76)
        bme.sea_level_pressure = 1013.25
        temp = str(bme.temperature)
        pressure = bme.pressure
        humidity = bme.humidity
        gas_primary = bme.gas
        gas = math.log(gas_primary) + 0.04 * math.log(gas_primary) / humidity * humidity

        machine.Pin(23, machine.Pin.OUT).high()
        sleep_ms(500)
        wlan = network.WLAN(network.STA_IF)
        network.hostname(UID)
        wlan.active(True)
        sleep_ms(500)
        wlan.connect(SSID, WIFI_PASSWORD)
        sleep_ms(500)

        i = 0
        total_retries = 0
        while not wlan.isconnected():
            print("Wi-Fi connecting...")
            if i > 30:
                raise Exception(
                    f"Wi-Fi connection failed. pin: {Pin(23).value()}, wlan: {wlan.status()}, retries: {total_retries}"
                )

            # STAT_GOT_IP: 3
            # STAT_CONNECTING: 1
            # STAT_IDLE: 0
            # STAT_CONNECT_FAIL: -1
            # STAT_WRONG_PASSWORD: -3
            # STAT_NO_AP_FOUND: -2
            status = wlan.status()
            if (
                status == network.STAT_CONNECT_FAIL
                or status == network.STAT_NO_AP_FOUND
            ):
                i = 0
                if total_retries > 5:
                    raise Exception(
                        f"Wi-Fi connection failed. pin: {machine.Pin(23).value()}, wlan: {wlan.status()}, retries: {total_retries}"
                    )
                wlan.connect(SSID, WIFI_PASSWORD)
                total_retries += 1

            sleep_ms(1000)
            i += 1

        client = mqtt_connect()
        sleep_ms(500)
        publish_temp(client, temp)
        publish_humidity(client, humidity)
        publish_pressure(client, pressure)
        publish_gas(client, gas)
        sleep_ms(500)
        wlan.disconnect()
        sleep_ms(500)
        wlan.active(False)
        sleep_ms(500)
        machine.Pin(23, machine.Pin.OUT).low()

    except Exception as e:
        if DEBUG:
            print(e)
            with open("error.log", "a+") as file:
                file.write(f"Error: {e}\n")

    sleep_ms(1000)
    machine.deepsleep(INTERVAL * 1000)


main()
