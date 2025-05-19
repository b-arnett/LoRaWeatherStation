# PWM Led Test
# Ben Arnett
# 04/10/2025

import time
import board
import pwmio

redled = pwmio.PWMOut(board.GP3, frequency=5000, duty_cycle=0)
#grnled = pwmio.PWMOut(board.GP17, frequency=5000, duty_cycle=0)

while True:
    for i in range(100):
        if i < 50:
            redled.duty_cycle = int(i * 2 * 65535 / 100)  # Up
            #grnled.duty_cycle = 65535 - int(i * 2 * 65535 /100) # Down
        else:
            redled.duty_cycle = 65535 - int((i - 50) * 2 * 65535 / 100)  # Down
            #grnled.duty_cycle = int((i-50) * 2 * 65535 / 100) # Up
        time.sleep(0.05)