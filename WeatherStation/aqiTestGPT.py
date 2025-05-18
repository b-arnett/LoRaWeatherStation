# ChatGPT AQI converter
import time
import board
import busio
import adafruit_pm25
from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C
# Initialize I2C communication and the PMSA003I sensor

i2c = busio.I2C(board.GP9, board.GP8, frequency=100000)
# Connect to a PM2.5 sensor over I2C
pms = PM25_I2C(i2c)


def calculate_aqi(pm25):
    """
    Converts PM2.5 concentration (µg/m³) into an AQI value
    using the US EPA AQI breakpoints.

    Args:
        pm25 (float): PM2.5 concentration in µg/m³

    Returns:
        float: Corresponding AQI value
    """

    # AQI breakpoints for PM2.5 (µg/m³) based on US EPA standards
    breakpoints = [
        (0.0, 12.0, 0, 50),       # Good
        (12.1, 35.4, 51, 100),    # Moderate
        (35.5, 55.4, 101, 150),   # Unhealthy for sensitive groups
        (55.5, 150.4, 151, 200),  # Unhealthy
        (150.5, 250.4, 201, 300), # Very unhealthy
        (250.5, 350.4, 301, 400), # Hazardous
        (350.5, 500.4, 401, 500)  # Hazardous
    ]

    # Find the corresponding AQI range for the given PM2.5 value
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= pm25 <= c_high:
            # Apply the AQI formula for linear interpolation
            return ((i_high - i_low) / (c_high - c_low)) * (pm25 - c_low) + i_low

    # If PM2.5 is higher than the highest breakpoint, return max AQI value
    return 500  # AQI maxes out at 500

while True:
    # Read air quality data from the PMSA003I sensor
    data = pms.read()
    
    # Extract the PM2.5 standard concentration in µg/m³
    pm25 = data["pm25 standard"]
    
    # Convert PM2.5 concentration to AQI
    aqi = calculate_aqi(pm25)
    
    # Print the results
    print(f"PM2.5: {pm25} µg/m³ -> AQI: {round(aqi)}")
    
    # Wait 10 seconds before taking the next reading
    time.sleep(10)