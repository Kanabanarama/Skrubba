# Skrubba

[![Build Status](https://scrutinizer-ci.com/g/Kanabanarama/Skrubba/badges/build.png?b=master)](https://scrutinizer-ci.com/g/Kanabanarama/Skrubba/build-status/master) [![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/Kanabanarama/Skrubba/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/Kanabanarama/Skrubba/?branch=master)

Backend for Raspberry Pi based plant irrigation system

#### HARDWARE:

- Raspberry Pi (A+ or similar)
- (din rail) 12V power supply
- Relay board with 8 relays
- step down regulator 5V
- female to female jumper wire
- 8x 12V solenoid valves
- RS-232 serial cable
- molex cable from computer power supply

#### PCB

![PCB](gfx/relaypcb01.png)

#### WIRING:

(COMING SOON)

#### CONFIGURATION

1. Install rasbpian (tested with stretch):

https://www.raspberrypi.org/downloads/raspbian/

1.1 Set timezone

# List timezones with: timedatectl list-timezones
# Set your timezone with: sudo timedatectl set-timezone <your timezone>
sudo timedatectl set-timezone Europe/Paris

2. On the "boot" partition of your raspberry, create a file "ssh".

3. Create a file wpa_supplicant.conf with the content below:

```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=DE

network={
     ssid="YOUR SSID"
     psk="YOUR WPA/WPA2 KEY"
     key_mgmt=WPA-PSK
}
```

4. Change the hostname by using the following commands in the pi's ssh or uart console

```
# To use bonjour service to access skrubba with skrubbal.local in your local network
sudo hostname skrubba
sudo sed -i 's/raspberrypi/skrubba/g' /etc/hosts
sudo sed -i 's/raspberrypi/skrubba/g' /etc/hostname
```

5. Activate SPI by uncommenting the following line into config.txt

```
dtparam=spi=on
```

6. Enable the display

```
# To test if the display is connected properly (you should see console output)
sudo modprobe fbtft_device name=waveshare32b rotate=90 gpios=reset:25,dc:24,cs:8

# To make it permanent, create a file /etc/modules-load.d/fbtft.conf
spi-bcm2835
fbtft_device

# Create a file /etc/modprobe.d/fbtft.conf
fbtft_device name=waveshare32b rotate=90 txbuflen=32768 gpios=reset:25,dc:24,cs:8

# Optional: replace content of /boot/cmdline.txt to see the boot process on the display
dwc_otg.lpm_enable=0 console=ttyAMA0,115200 console=tty1 root=/dev/mmcblk0p2 rootfstype=ext4 elevator=deadline rootwait fbtft_device.name=waveshare32b fbtft_device.rotate=90 fbtft_device.txbuflen=32768 fbtft_device.gpios=reset:25,dc:24,cs:8 fbcon=map:10 fbcon=font:VGA8x8fbcon=rotate:1
```

#### INSTALLATION

Install the required packages

```
sudo apt-get update && apt-get upgrade
sudo apt-get install git python3 python3-pip python3-venv python3-flask python3-apscheduler python3-pygame python3-rpi.gpio

# Clone the skrubba repository
git clone https://github.com/Kanabanarama/Skrubba skrubba
```

#### USAGE

Test the skrubba webserver

```
sudo python3 ~/skrubba/main.py & disown
```

COMING SOON: gunicorn + autostart
