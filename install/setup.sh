#!/bin/sh

# supervisor conf
echo "Setting up supervisor"
sudo cp /home/pi/skrubba/install/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

sudo supervisorctl reread
sudo service supervisor restart
sudo supervisorctl status

# nginx conf
echo "Setting up nginx"
sudo cp /home/pi/skrubba/install/skrubba.conf /etc/nginx/sites-available/skrubba.conf
sudo ln -fs /etc/nginx/sites-available/skrubba.nginx /etc/nginx/sites-enabled/skrubba
sudo [ -e /etc/nginx/sites-enabled/default ] && rm /etc/nginx/sites-enabled/default

sudo service nginx reload

echo "Finished setup"
