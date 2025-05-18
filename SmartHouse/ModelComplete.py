# Model Actuator Test
# Ben Arnett
# 05/12/2025
 
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

# Initialize Devices 
rylr = busio.UART(board.GP0, board.GP1, baudrate=9600)
i2c0 = busio.I2C(board.GP9, board.GP8, frequency=100000)

lcd = LCD1602(i2c0)
lcd.clear()
lcd.write('  Initializing')

whtled = pwmio.PWMOut(board.GP3, frequency=5000, duty_cycle=0)

servo_a_pin = pwmio.PWMOut(board.GP28, frequency=50)
servo_a = servo.Servo(servo_a_pin, min_pulse=1000, max_pulse=2000)

# 'Breathe' leds once, modulate servo to verify function
for i in range(100):
        if i < 50:
            whtled.duty_cycle = int(i * 2 * 65535 / 100)  # Up
        else:
            whtled.duty_cycle = 65535 - int((i - 50) * 2 * 65535 / 100)  # Down
        time.sleep(0.025)

whtled.duty_cycle = 0

servo_a.angle = 0
time.sleep(0.5)
servo_a.angle = 20
time.sleep(0.5)
servo_a.angle = 40
time.sleep(0.5)
servo_a.angle = 60
time.sleep(0.5)
servo_a.angle = 70
time.sleep(0.5)

lcd.clear()
lcd.set_cursor(2, 0)
lcd.write('Waiting for')
lcd.set_cursor(2, 1)
lcd.write('Weather Data')
print("Init complete, waiting for data")

recieved = False

# Function to parse new recieved data
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
    return result # returns a dictionary

# Function to change interior conditions
def interior(d):
    light = d['L']
    # If its pretty bright, open blinds and turn off lights
    if light > 3:
        whtled.duty_cycle = 0
        servo_a.angle = 15
        return
    
    involt = 3 - light
    lightduty = round(involt * 18000) # inverted scaling
    servangle = round(18 * involt) + 15 # regular scaling
    
    print('lightduty = {0} servangle = {1}'.format(lightduty, servangle))
    
    whtled.duty_cycle = lightduty
    servo_a.angle = servangle
    return


# Function to update stats on display 
def lcddisplay(d):
    if recieved == False:
        lcd.clear()
        lcd.write('T:  C Light:   %')
        lcd.set_cursor(0, 1)
        lcd.write('AQI:    RH:   %')
    
    lightperc = round(d['L'] / 3.2 * 100)
    
    lcd.set_cursor(2, 0)
    if d['T'] < 10:
        lcd.write(" ")
    lcd.write(str(d['T']))
    lcd.set_cursor(12, 0)
    lcd.write(lcdform(lightperc))
    lcd.set_cursor(4, 1)
    lcd.write(lcdform(d['AQI']))
    lcd.set_cursor(11, 1)
    lcd.write(str(lcdform(round(d['RH']))))
    return
    # T:00C Light:00%
    # _AQI:000 RH:00%

# Format data to write properly
def lcdform(number):
    stringout = ""
    if number < 10:
        stringout = stringout + "  "
    elif number < 100:
        stringout = stringout + " "
    stringout = stringout + str(number)
    return stringout
        
# Main Loop
while True:
    data = rylr.read()
    
    if data is not None:
        # Make a string with incoming data, then put it through the parser
        data_string = ''.join([chr(b) for b in data])
        print(data_string, end="")
        parsed = parse_sensor_data(data_string)
        print(parsed)
        
        # Update display and Interior settings
        lcddisplay(parsed)
        interior(parsed)
        recieved = True
      
    else:
        if recieved == False:
            time.sleep(0.05)

