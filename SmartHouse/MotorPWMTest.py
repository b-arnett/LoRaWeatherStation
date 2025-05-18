# PWM Motor Driver Test
# Ben Arnett
# 04/10/2025

import time
import pwmio
import board

# For PWM with circuitpython, 65535 is 100%, 0 is 0% duty cycle

motor = pwmio.PWMOut(board.GP21, frequency=50, duty_cycle=0)

while True:
    for i in range(20):
        if i < 10:
            motor.duty_cycle = int(i * 800)  # Up
        else:
            motor.duty_cycle = 8000 - int((i - 10) * 800)  # Down
        time.sleep(1)
    
        