import board
import busio
import adafruit_bme680
import time

i2c = busio.I2C(board.GP9, board.GP8)
sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c)

sensor.seaLevelhPa = 1011


while True:
    
    print('Temperature: {} degrees C'.format(sensor.temperature))
    print('Gas: {} ohms'.format(sensor.gas))
    print('Humidity: {}%'.format(sensor.humidity))
    print('Pressure: {}hPa'.format(sensor.pressure))
    print('Altitude: {} meters'.format(sensor.altitude))
    print("---------------------------------")
    time.sleep(1)