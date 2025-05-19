import board
import busio
import digitalio
import time
from lcd1602 import LCD1602

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

uart = busio.UART(board.GP0, board.GP1, baudrate=9600)
i2c = busio.I2C(board.GP9, board.GP8, frequency=100000)
lcd = LCD1602(i2c)
'''
class ReceivedMessage:
    def __init__(self) -> None:
        self.address:int = None # the address of the transmitter it came from
        self.length:int = None # the length (number of bytes) of the data payload
        self.data:bytes = None # the payload data itself
        self.RSSI:int = None # Received signal strength indicator
        self.SNR:int = None # Signal-to-noise ratio

    def parse(self, full_line:bytes) -> None:
        """Parses a received message from the raw line of byte data received over UART. For example, b'+RCV=50,5,HELLO,-99,40'"""

        try:

            # find landmarkers that will help with parsing
            i_equal:int = full_line.find("=".encode("ascii"))
            i_comma1:int = full_line.find(",".encode("ascii"))
            i_comma2:int = full_line.find(",".encode("ascii"), i_comma1 + 1)
            i_comma4:int = full_line.rfind(",".encode("ascii")) # search from end
            i_comma3:int = full_line.rfind(",".encode("ascii"), 0, i_comma4-1) # search for a comma from right, starting at 0 and ending at the last comma (or right before it)
            i_linebreak:int = full_line.find("\r\n".encode("ascii"))
            
            # extract
            self.ReceivedMessage = ReceivedMessage()
            self.address = int(full_line[i_equal + 1:i_comma1].decode("ascii"))
            self.length = int(full_line[i_comma1 + 1:i_comma2].decode("ascii"))
            self.data = full_line[i_comma2 + 1:i_comma3]
            self.RSSI = int(full_line[i_comma3 + 1:i_comma4].decode("ascii"))
            self.SNR = int(full_line[i_comma4 + 1:i_linebreak].decode("ascii"))
        except Exception as e:
            raise Exception("Unable to parse line '" + str(full_line) + "' as a ReceivedMessage! Exception message: " + str(e))

    def __str__(self) -> str:
        return str({"address":self.address, "length":self.length, "data":self.data, "RSSI":self.RSSI, "SNR":self.SNR})
'''
def parse_sensor_data(data: str) -> dict:
    result = {}
    address:int = None # the address of the transmitter it came from
    length:int = None # the length (number of bytes) of the data payload
    msg:bytes = None # the payload data itself
    RSSI:int = None # Received signal strength indicator
    SNR:int = None # Signal-to-noise ratio
    
    try:

            # find landmarkers that will help with parsing
            i_equal:int = data.find("=")
            i_comma1:int = data.find(",")
            i_comma2:int = data.find(",", i_comma1 + 1)
            i_comma4:int = data.rfind(",") # search from end
            i_comma3:int = data.rfind(",", 0, i_comma4-1) # search for a comma from right, starting at 0 and ending at the last comma (or right before it)
           # i_linebreak:int = data.find("\r\n")
            
            # extract
            ReceivedMessage = data
            address = int(data[i_equal + 1:i_comma1])
            length = int(data[i_comma1 + 1:i_comma2])
            msg = data[i_comma2 + 1:i_comma3]
            RSSI = int(data[i_comma3 + 1:i_comma4])
            #SNR = int(data[i_comma4 + 1:i_linebreak])
    except Exception as e:
            raise Exception("Unable to parse line '" + str(data) + "' as a ReceivedMessage! Exception message: " + str(e))

    pairs = msg.split(";")  # Split the string into key-value pairs
    for pair in pairs:
        if ":" in pair:
            key, value = pair.split(":")  # Separate key and value
            # Try to convert value to int or float if possible
            if value.replace(".", "", 1).isdigit():
                value = float(value) if "." in value else int(value)
            result[key] = value
    return result

# Example usage
#data_string = "Led=1;Temp=77;Light=0.85"
#parsed_data = parse_sensor_data(data_string)
#print(parsed_data)
i = 0
recieved = False

while True:
    data = uart.read()
    
    if data is not None:
        led.value = True
        data_string = ''.join([chr(b) for b in data])
        print(data_string, end="")
        parsed = parse_sensor_data(data_string)
        print(parsed)
        lcd.write("Recieved! \n #: " + str(i))
        led.value = False
        recived = True
        i += 1
        
    else:
        if recieved == False:
            lcd.clear()
            lcd.write("Waiting...")
            print("waiting")
            time.sleep(0.05)
            
        else:
            time.sleep(0.05)
            
