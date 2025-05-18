# Servo Test


from time import sleep
import board
import pwmio
from adafruit_motor import servo

DEBUG = True

servo_a_pin = pwmio.PWMOut(board.GP18, frequency=50)
servo_a = servo.Servo(servo_a_pin, min_pulse=1000, max_pulse=2000)
def basic_operations():
    if DEBUG: print("Setting angle to 90 degrees.")
    servo_a.angle = 90
    sleep(3)
    if DEBUG: print("Setting angle to 0 degrees.")
    servo_a.angle = 0
    sleep(3)
    if DEBUG: print("Setting angle to 90 degrees.")
    servo_a.angle = 90
    sleep(3)
    if DEBUG: print("Setting angle to 180 degrees.")
    servo_a.angle = 180
    sleep(3)
while True:
    basic_operations()