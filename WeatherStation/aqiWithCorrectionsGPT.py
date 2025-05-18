# AQI with BME688 based correction factors
# From ChatGPT, with adjustments made by Ben A.

import time
import board
import busio
import adafruit_bme680  # Works for BME688 too
import adafruit_pm25
from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C

# Initialize I2C communication and the PMSA003I sensor
i2c = busio.I2C(board.GP9, board.GP8, frequency=100000)
# Connect to a PM2.5 sensor over I2C
pms = PM25_I2C(i2c)

# Initialize BME688 sensor
bme = adafruit_bme680.Adafruit_BME680_I2C(i2c)

def correct_pm25(pm25, humidity, temperature):
    """
    Applies correction factors to PM2.5 based on humidity and temperature.

    Args:
        pm25 (float): Raw PM2.5 measurement (µg/m³)
        humidity (float): Relative humidity (%)
        temperature (float): Temperature (°C)

    Returns:
        float: Corrected PM2.5 value
    """
    # Humidity correction (EPA formula)
    humidity_correction = 1 + 0.487 * (2.718 ** (0.059 * humidity))
    pm25_corrected = pm25 / humidity_correction

    # Temperature correction
    temp_correction_factor = 1 - 0.02 * (temperature - 25)
    pm25_corrected *= temp_correction_factor

    return pm25_corrected

while True:
    # Read sensor data
    pms_data = pms.read()
    pm25_raw = pms_data["pm25 standard"]

    humidity = bme.relative_humidity
    temperature = bme.temperature

    # Apply correction
    pm25_corrected = correct_pm25(pm25_raw, humidity, temperature)

    # Print results
    print(f"PM2.5 Raw: {pm25_raw:.2f} µg/m³")
    print(f"PM2.5 Corrected: {pm25_corrected:.2f} µg/m³")
    print(f"Temperature: {temperature:.2f} °C, Humidity: {humidity:.2f} %")
    print("-" * 40)

    time.sleep(10)