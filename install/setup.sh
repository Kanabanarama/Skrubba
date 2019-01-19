#!/bin/sh

# create virtualenv
echo "Setting up python3 virtual environment"
python3 -m venv /home/pi/skrubba/.venv
. .venv/bin/activate

# pip packages
echo "Installing required python3 packages"
pip3 install -r /home/pi/skrubba/requirements.txt

# supervisor conf
echo "Setting up supervisor"
sudo cp /home/pi/skrubba/install/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

sudo supervisorctl reread
sudo service supervisor restart
sudo supervisorctl status

# nginx conf
echo "Setting up nginx"
sudo cp /home/pi/skrubba/install/skrubba.conf /etc/nginx/sites-available/skrubba
sudo ln -fs /etc/nginx/sites-available/skrubba /etc/nginx/sites-enabled/skrubba
sudo [ -e /etc/nginx/sites-enabled/default ] && rm /etc/nginx/sites-enabled/default

sudo service nginx reload

echo "Finished setup"
