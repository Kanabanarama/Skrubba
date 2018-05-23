from time import sleep
from display import Display

tft = Display()
#tft.setBackgroundColor(255, 255, 255)
tft.displayImage('static/gfx/lcd-skrubba-color.png', x = 67, y = 10, clearScreen = True)
while True:
    sleep(10)
