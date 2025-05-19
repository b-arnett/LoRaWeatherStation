# ADC test for photo transistor
# BA 03/11/25

import time
import busio
import board
import analogio

ptr = analogio.AnalogIn(board.GP26)

# Pico ADC is 12 bits, so need to scale to 16 bits to work with CircuitPython's API

def stepstovolt(step):
    return (step * 3.3) / 65536
#							2^16


while True:
    steps = ptr.value
    voltage = stepstovolt(steps)
    print('Steps: {} Voltage: {:1.3}'.format(steps, voltage))
    time.sleep(0.5)
    