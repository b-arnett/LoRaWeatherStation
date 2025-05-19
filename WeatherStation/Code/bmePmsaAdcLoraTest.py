# bmePmsaAdcLoraTest.py

import time
import board
import busio
import analogio
import adafruit_bme680
from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C


reset_pin = None
# If you have a GPIO, its not a bad idea to connect it to the RESET pin
# reset_pin = DigitalInOut(board.G0)
# reset_pin.direction = Direction.OUTPUT
# reset_pin.value = False


# Create library object, use 'slow' 100KHz frequency!
i2c = busio.I2C(board.GP9, board.GP8, frequency=100000)
# Connect to a PM2.5 sensor over I2C

# PMSA003i
pms = PM25_I2C(i2c, reset_pin)
print("Found PMSA003i")

# BME688
sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c)
sensor.seaLevelhPa = 1011
print("Found BME688")

# Rylr993 lite 
uart = busio.UART(board.GP0, board.GP1, baudrate=9600)
print("UART bus enabled")

# PhotoTransistor 
ptv = analogio.AnalogIn(board.GP26)
print("Photo Transistor Found")

# Address of Rylr module to send to 
address = 6

def rylr_send(message):
    length = len(message)
    send = 'AT+SEND={},{},{}\r\n'.format(address, length, message)
    uart.write(send.encode("ascii"))
    print('Data send to {}'.format(address))
    
def correct_pm25(pm25, humidity, temperature):
    """
    Applies correction factors to PM2.5 based on humidity and temperature.

    Args:
        pm25 (float): Raw PM2.5 measurement (µg/m³)
        humidity (float): Relative humidity (%)
        temperature (float): Temperature (°C)

    Returns:
        float: Corrected PM2.5 value
    """
    # Humidity correction (EPA formula)
    humidity_correction = 1 + 0.487 * (2.718 ** (0.059 * humidity))
    pm25_corrected = pm25 / humidity_correction

    # Temperature correction
    temp_correction_factor = 1 - 0.02 * (temperature - 25)
    pm25_corrected *= temp_correction_factor

    return pm25_corrected


def ptvoltage(adcin):
    steps = 0
    i = 0
    while i < 8:
        steps += adcin.value
        time.sleep(0.5)
        i += 1
    
    steps = steps/8
    i = 0
    # Pico ADC is 12 bits, so need to scale to 16 bits to work with CircuitPython's API
    return (steps * 3.3) / 65536
    #						2^16
    
# apply significant figures to readings
def fivesf(num):
    sfnum = "{:5.2}".format(num)
    return sfnum

# Time Tracker variables
seconds = 0
minutes = 0

# time (s) between readings
intervaltime = 5

while True:
    time.sleep(intervaltime)

    try:
        aqdata = pms.read()
        # print(aqdata)
    except RuntimeError:
        print("Unable to read from sensor, retrying...")
        continue
    
    # get raw aqi
    
    pms_data = pms.read()
    pm25_raw = pms_data["pm25 standard"]

    humidity = sensor.relative_humidity
    temperature = sensor.temperature
    pressure = sensor.pressure
    altitude = sensor.altitude
    
    # get PhotoTransistor Voltage
    ptvolt = ptvoltage(ptv)
    
    # Apply correction
    pm25_corrected = correct_pm25(pm25_raw, humidity, temperature)
    
    # Apply significant figures
    pm25_corrected = "{:3.1f}".format(pm25_corrected)
    humidity = "{:2.1f}".format(humidity)
    temperature = "{:3.1f}".format(temperature)
    pressure = "{:4.1f}".format(pressure)
    altitude = "{:3.1f}".format(altitude)
    ptvolt = "{:1.2f}".format(ptvolt)
    
    msg = 'AQI: {0} T: {1}C\r{2}hPa Alt: {3}m Light: {4}v'.format(pm25_corrected, temperature, pressure, altitude, ptvolt)
    #lcd.write(msg)
    # format to be parse-able
    rylrmsg = 'AQI:{0};T(C):{1};Humidity(%):{2};Pressure(hPa):{3};Alt(m):{4};Light(V):{5}'.format(pm25_corrected, temperature, humidity, pressure, altitude,ptvolt)
    rylr_send(rylrmsg)
    
    
    print()
    print("Concentration Units (standard)")
    print("---------------------------------------")
    print(
        "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
        % (aqdata["pm10 standard"], aqdata["pm25 standard"], aqdata["pm100 standard"])
    )
    print("Concentration Units (environmental)")
    print("---------------------------------------")
    print(
        "PM 1.0: %d\tPM2.5: %d\tPM10: %d"
        % (aqdata["pm10 env"], aqdata["pm25 env"], aqdata["pm100 env"])
    )
    print("---------------------------------------")
    print("Corrected AQI")
    print(str(pm25_corrected))
    print("---------------------------------------")
    print("Particles > 0.3um / 0.1L air:", aqdata["particles 03um"])
    print("Particles > 0.5um / 0.1L air:", aqdata["particles 05um"])
    print("Particles > 1.0um / 0.1L air:", aqdata["particles 10um"])
    print("Particles > 2.5um / 0.1L air:", aqdata["particles 25um"])
    print("Particles > 5.0um / 0.1L air:", aqdata["particles 50um"])
    print("Particles > 10 um / 0.1L air:", aqdata["particles 100um"])
    print("---------------------------------------")
    print('Temperature: {} degrees C'.format(sensor.temperature))
    print('Gas: {} ohms'.format(sensor.gas))
    print('Humidity: {}%'.format(sensor.humidity))
    print('Pressure: {}hPa'.format(sensor.pressure))
    print('Altitude: {} meters'.format(sensor.altitude))
    print("---------------------------------------")
    print('Time since init: {0} m {1} s'.format(minutes, seconds))
    print("---------------------------------------")
    
    seconds += intervaltime
    if seconds >= 60:
        minutes += 1
        extra = seconds % 60
        if extra != 0:
            seconds = extra
        else:
            seconds = 0
        
        
