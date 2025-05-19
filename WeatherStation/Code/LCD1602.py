# GPT Rewritten driver for 16x2 character LCD

import time
import board
import busio
from adafruit_bus_device.i2c_device import I2CDevice

class LCD1602:
    def __init__(self, i2c, address=0x27, backlight=True):
        """
        Initializes the LCD1602 display.
        :param i2c: The I2C bus object.
        :param address: I2C address of the LCD (default: 0x27).
        :param backlight: Whether to enable the backlight (default: True).
        """
        self.device = I2CDevice(i2c, address)
        self.address = address
        self.backlight = 0x08 if backlight else 0x00
        
        # Initialize display
        self.send_command(0x33)  # Initialize to 8-bit mode
        time.sleep(0.005)
        self.send_command(0x32)  # Switch to 4-bit mode
        time.sleep(0.005)
        self.send_command(0x28)  # 2-line display, 5x7 font
        self.send_command(0x0C)  # Display on, cursor off
        self.send_command(0x01)  # Clear display
        time.sleep(0.005)
    
    def send_command(self, cmd):
        """Send a command to the LCD."""
        self._write(cmd, 0)
    
    def send_data(self, data):
        """Send data (characters) to the LCD."""
        self._write(data, 1)
    
    def _write(self, value, mode):
        """
        Write data or command to LCD.
        :param value: The byte to send.
        :param mode: 0 for command, 1 for data.
        """
        high_nibble = (value & 0xF0) | self.backlight | mode
        low_nibble = ((value << 4) & 0xF0) | self.backlight | mode
        self._i2c_write(high_nibble)
        self._i2c_write(low_nibble)
    
    def _i2c_write(self, data):
        """Write a byte to the I2C device."""
        with self.device as i2c:
            i2c.write(bytes([data | 0x04]))  # Enable bit high
            time.sleep(0.001)
            i2c.write(bytes([data & ~0x04]))  # Enable bit low
            time.sleep(0.001)
    
    def clear(self):
        """Clear the display."""
        self.send_command(0x01)
        time.sleep(0.002)
    
    def set_cursor(self, col, row):
        """Set the cursor position."""
        positions = [0x80, 0xC0]  # Address for row 0 and 1
        self.send_command(positions[row] + col)
    
    def write(self, text):
        """Write text to the display."""
        for char in text:
            self.send_data(ord(char))

# Example usage
# if __name__ == "__main__":
  #   i2c = busio.I2C(board.SCL, board.SDA)
   #  lcd = LCD1602(i2c)
    # lcd.write("Hello, World!")
