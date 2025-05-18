# WSMainSend.py
# Ben Arnett


import time
import board
import busio
import analogio
import adafruit_bme680
import digitalio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C


reset_pin = None
# If you have a GPIO, its not a bad idea to connect it to the RESET pin
# reset_pin = DigitalInOut(board.G0)
# reset_pin.direction = Direction.OUTPUT
# reset_pin.value = False

pwr = digitalio.DigitalInOut(board.GP15)
pwr.direction = digitalio.Direction.OUTPUT
pwr.value = True


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
pt = analogio.AnalogIn(board.GP26)
print("Photo Transistor Found")

# Address of Rylr module to send to 
address = 6

def rylr_send(message):
    length = len(message)
    send = 'AT+SEND={},{},{}\r\n'.format(address, length, message)
    uart.write(send.encode("ascii"))
    print('Data sent to {}'.format(address))
    
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
    #						2^16
    
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
    
    # get raw aqi
    
    pms_data = pms.read()
    pm25_raw = pms_data["pm25 standard"]

    humidity = sensor.relative_humidity
    temperature = sensor.temperature
    pressure = sensor.pressure
    altitude = sensor.altitude
    
    # get PhotoTransistor Voltage
    ptvolt = ptvoltage(pt)
    
    # Apply correction
    pm25_corrected = correct_pm25(pm25_raw, humidity, temperature)
    
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
    time.sleep(30) # change to 15 mins / 870s off, 30ish on
        
        
