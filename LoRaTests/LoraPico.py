# Rylr998 Test Send

import board
import busio
import digitalio
import time

uart = busio.UART(board.GP0, board.GP1, baudrate=115200)
test = 0
send = "AT+SEND=6,4,test\r\n"

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
ledState = False


while True:
    led.value = True    
    uart.write(send.encode("ascii"))
    print("sent")
    time.sleep(2.5)
    led.value = False
    time.sleep(2.5)
    