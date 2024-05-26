import serial
import time
rs232 = None
# ------------------------------------------------------------------------------
try:
    rs232 = serial.Serial(port='COM11', baudrate=115200, timeout=2)
except:
    print("Serial port not found")

print(rs232.isOpen)
if rs232.isOpen() == True:
    while True:
        size = rs232.inWaiting()
        if size:
            data = rs232.read(size)
            print(data)
        else:
            print('No Data Found!')
        time.sleep(1)
else:
    print('rs232 is not open.')
    rs232.close()