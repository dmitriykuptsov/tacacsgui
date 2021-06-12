#!/bin/bash

sudo apt-get install python3
sudo apt-get install python3-pip
sudo apt-get install mysql-server
sudo apt-get install mysql-client
echo "Would you like to configure MySQL? (Y/N)"
read answer
if [[ "$answer" == "Y" || "$answer" == "y" ]]
then
	sudo mysql_secure_installation
fi

sudo apt-get install python3-mysqldb

sudo pip3 install flask
sudo pip3 install flask_wtf
sudo pip3 install flask-sqlalchemy
sudo pip3 install sqlalchemy

echo "Creating TACACSGUI folder"
sudo mkdir -p /opt/tacacsgui
sudo chown www-data:www-data -R /opt/tacacsgui

mysql -uroot -pNigAfDov < ../database/schema.sql

sudo rsync -rv ../app ../run.py ../config.py /opt/tacacsgui/

sudo rsync -rv ../systemd/tacacsgui.service /etc/systemd/system/
sudo systemctl enable tacacsgui
sudo systemctl start tacacsgui
