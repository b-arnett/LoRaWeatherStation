# WSMainSend.py
# Ben Arnett
# 05/12/2025

import time
import board
import busio
import analogio
import adafruit_bme680
import digitalio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C


reset_pin = None

# Setup IO pin to turn on and off PMSA03i
pwr = digitalio.DigitalInOut(board.GP15)
pwr.direction = digitalio.Direction.OUTPUT
pwr.value = True


# Create library object, use 'slow' 100KHz frequency!
i2c = busio.I2C(board.GP9, board.GP8, frequency=100000)

# Connect to a PMSA003i over I2C
pms = PM25_I2C(i2c, reset_pin)
print("Found PMSA003i")

# Connect to BME688 over I2C
# note: BME688 uses the bme680 library
sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c)
sensor.seaLevelhPa = 1011
print("Found BME688")

# Init UART bus for RYLR993 lite
uart = busio.UART(board.GP0, board.GP1, baudrate=9600)
print("UART bus enabled")

# PhotoTransistor setup
pt = analogio.AnalogIn(board.GP26)
print("Photo Transistor Found")

# Address of Rylr module to send to 
address = 6

# Function to send LoRa messages with the RYLR
def rylr_send(message):
    length = len(message)
    send = 'AT+SEND={},{},{}\r\n'.format(address, length, message)
    uart.write(send.encode("ascii"))
    print('Data sent to {}'.format(address))
    
# Function to apply AQI correction calculations
def correct_pm25(pm25, humidity, temperature):
    # correction calculations from ChatGPT
    # Humidity correction (EPA formula)
    humidity_correction = 1 + 0.487 * (2.718 ** (0.059 * humidity))
    pm25_corrected = pm25 / humidity_correction

    # Temperature correction
    temp_correction_factor = 1 - 0.02 * (temperature - 25)
    pm25_corrected *= temp_correction_factor

    return pm25_corrected

# Get Light sensor voltage
def ptvoltage(adcin):
    steps = 0
    i = 0
    # get average over 4 seconds
    while i < 20:
        steps += adcin.value
        time.sleep(0.2)
        i += 1
    
    steps = steps/20
    
    # Pico ADC is 12 bits, so need to scale to 16 bits to work with CircuitPython's API
    return (steps * 3.3) / 65536
    
# Main Loop
while True:
    # Turn on PMSA, give 30s to warmup
    pwr.value = True
    print("Turned on PMSA, 30s warmup")
    time.sleep(30)
    print("Reading Sensors")
    
    try:
        aqdata = pms.read()
        # print(aqdata)
    except RuntimeError:
        print("Unable to read from sensor, retrying...")
        continue
    
    # get raw PM 2.5 concentration and apply corrections
    
    pms_data = pms.read()
    pm25_raw = pms_data["pm25 standard"]
    pm25_corrected = correct_pm25(pm25_raw, humidity, temperature)
	
    # get BME688 sensor data
    humidity = sensor.relative_humidity
    temperature = sensor.temperature
    pressure = sensor.pressure
    altitude = sensor.altitude
    
    # get PhotoTransistor Voltage
    ptvolt = ptvoltage(pt)
    
    # Apply significant figures
    pm25_corrected = round(pm25_corrected) 
    humidity = "{:2.1f}".format(humidity)
    temperature = round(temperature) # 3 Digits
    pressure = round(pressure) # 
    altitude = round(altitude)
    ptvolt = "{:1.2f}".format(ptvolt) # 3 dig. 4 char
    
    # format to be parse-able
    rylrmsg = 'AQI:{0};T:{1};RH:{2};hPa:{3};Alt:{4};L:{5}'.format(pm25_corrected, temperature, humidity, pressure, altitude, ptvolt)
    rylr_send(rylrmsg)
    print(rylrmsg)
    
    # Turn off PMSA
    pwr.value = False
    print("Turned off PMSA, light sleeping")
    # Light sleep till next reading
    time.sleep(866) # Sleep 14m 26s (15 mins between data transmissions)
		    # ^ account for 30s PMSA on time & 4s light volt reading
        
        
