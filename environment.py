import os

# because there is no 64 bit version of pygame and the display is installed
# on the raspberry pi, not on the development system, omit the import
RUNNINGONPI = os.uname()[4][:3] == 'arm'