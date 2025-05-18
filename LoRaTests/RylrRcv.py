import board
import busio
import digitalio
import time

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

uart = busio.UART(board.GP0, board.GP1, baudrate=9600)


while True:
    data = uart.read()
    
    if data is not None:
        led.value = True
        data_string = ''.join([chr(b) for b in data])
        print(data_string, end="")

        led.value = False
        
    else:
        
        print("waiting")
        time.sleep(0.05)