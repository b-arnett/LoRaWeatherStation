# Model Actuator Test
# Ben Arnett
# 04/10/2025
 
# UART = GP 0,1
# I2C = SDA-GP8, SCL-GP9
# Led PWM = GP5
# Servo PWM = GP28

import board
import busio
import digitalio
import time
import pwmio
from lcd1602 import LCD1602
from adafruit_motor import servo

# Init Devices 
rylr = busio.UART(board.GP0, board.GP1, baudrate=9600)
# i2c0 = busio.I2C(board.GP9, board.GP8, frequency=100000)
# lcd = LCD1602(i2c0)

whtled = pwmio.PWMOut(board.GP3, frequency=5000, duty_cycle=0)

servo_a_pin = pwmio.PWMOut(board.GP28, frequency=50)
servo_a = servo.Servo(servo_a_pin, min_pulse=1000, max_pulse=2000)

# pulse lights, servo to show its working

for i in range(100):
        if i < 50:
            whtled.duty_cycle = int(i * 2 * 65535 / 100)  # Up
            #grnled.duty_cycle = 65535 - int(i * 2 * 65535 /100) # Down
        else:
            whtled.duty_cycle = 65535 - int((i - 50) * 2 * 65535 / 100)  # Down
            #grnled.duty_cycle = int((i-50) * 2 * 65535 / 100) # Up
        time.sleep(0.025)

whtled.duty_cycle = 0

servo_a.angle = 0
time.sleep(0.5)
servo_a.angle = 30
time.sleep(0.5)
servo_a.angle = 60
time.sleep(0.5)
servo_a.angle = 90
time.sleep(0.5)
servo_a.angle = 0


print("Init complete, waiting for data")

# Modified for circuitpython from https://github.com/TimHanewich/MicroPython-Collection/blob/master/REYAX-RYLR998/
def parse_sensor_data(data: str) -> dict:
    # Extract the weather data from entire recieved byte data
    result = {}
    address:int = None # the address of the transmitter it came from
    length:int = None # the length (number of bytes) of the data payload
    msg:bytes = None # the payload data itself
    RSSI:int = None # Received signal strength indicator
    SNR:int = None # Signal-to-noise ratio
    
    try:
            # find landmarkers that will help with parsing
            i_equal:int = data.find("=")
            i_comma1:int = data.find(",")
            i_comma2:int = data.find(",", i_comma1 + 1)
            i_comma4:int = data.rfind(",") # search from end
            i_comma3:int = data.rfind(",", 0, i_comma4-1) # search for a comma from right, starting at 0 and ending at the last comma (or right before it)
           # i_linebreak:int = data.find("\r\n")
            
            # extract
            ReceivedMessage = data
            address = int(data[i_equal + 1:i_comma1])
            length = int(data[i_comma1 + 1:i_comma2])
            msg = data[i_comma2 + 1:i_comma3]
            RSSI = int(data[i_comma3 + 1:i_comma4])
            #SNR = int(data[i_comma4 + 1:i_linebreak])
    except Exception as e:
            raise Exception("Unable to parse line '" + str(data) + "' as a ReceivedMessage! Exception message: " + str(e))
    
    # Take the weather data string and turn into a dictionary
    # Modified from ChatGPT generated code
    pairs = msg.split(";")  # Split the string into key-value pairs
    for pair in pairs:
        if ":" in pair:
            key, value = pair.split(":")  # Separate key and value
            # Try to convert value to int or float if possible
            if value.replace(".", "", 1).isdigit():
                value = float(value) if "." in value else int(value)
            result[key] = value
    return result

# Call this when we want to update interior settings
def interior(d):
    if d['L'] < 1.5:  # Almost full brightness
        whtled.duty_cycle = 50000
        servo_a.angle = 30 # 1/3 open
    elif d['L'] < 2:  # 2/3 brightness
        whtled.duty_cycle = 42000
        servo_a.angle = 60 # 2/3 open
    elif d['L'] < 2.5:  # 1/3 brightness
        whtled.duty_cycle = 20000
        servo_a.angle = 90 # Fully open
    else:
        whtled.duty_cycle = 0
        servo_a.angle = 0 # Closed
    
recieved = False

while True:
    data = rylr.read()
    
    if data is not None:
        data_string = ''.join([chr(b) for b in data])
        print(data_string, end="")
        parsed = parse_sensor_data(data_string)
        print(parsed)
        lcddisplay = ('T: {}C \n AQI: {}'.format(parsed['T'], parsed['AQI']))
        '''lcd.clear()
        lcd.write('T: {}C'.format(parsed['T']))
        lcd.set_cursor(0, 1)
        lcd.write('AQI: {}'.format(parsed['AQI']))'''
        interior(parsed)
        recived = True
      
        
    else:
        if recieved == False:
            #lcd.clear()
            #lcd.write("Waiting...")
            #print("waiting")
            time.sleep(0.05)
            
        else:
            time.sleep(0.05)

#  Servo: Shutters based on ext light//  0 to 3.2V ish 
#   if 0 < L < 1 then Close shutters (at night want blinds closed)
#   if 1 < L < 2 then open shutters 1/4 way
#   if 2 < L < 2.5 then open 1/2 way
#   if 2.5 < L then open all the way (open during daytime for natural light)

# White Led (white in future):  Interior lights based on ext light
#   if 0 < L < 1 then lights 100% on
#   if 1 < L < 2 then lights 75% on
#   if 2 < L < 2.5 then lights 50% on
#   if 2.5 < L then lights 0% on i.e. off

