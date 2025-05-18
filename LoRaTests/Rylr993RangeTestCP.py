# Rylr993RangeTest.py
# Ben Arnett
# 03/04/25

import time
import board
import busio
import digitalio

# Only use with Rylr993 lite, not 998
rylr = busio.UART(board.GP0, board.GP1, baudrate=9600)

# address of Rylr on network to send to
addr = 27

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

i = 1


while True:
    led.value = True
    msg = "Test " + str(i)
    length = len(msg) 
    send = 'AT+SEND={},{},{}\r\n'.format(addr, length, msg)

    rylr.write(send.encode("ascii"))
    print("Just sent test " + str(i))
    led.value = False
    time.sleep(5)
    i += 1
            
