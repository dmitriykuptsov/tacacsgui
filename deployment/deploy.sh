#!/bin/bash
sudo apt-get install python3
sudo apt-get install python3-pip
sudo apt-get install mysql-server
sudo apt-get install mysql-client

echo "Would you like to configure MySQL? (Y/N)"
read answer
if [[ "$answer" == "Y" || "$answer" == "y" ]]
then
	echo "ALTER USER 'root'@'localhost' IDENTIFIED BY 'NigAfDov';" > reset.sql
	sudo mysql -uroot < reset.sql
	rm reset.sql
fi

sudo apt-get install python3-mysqldb

sudo pip3 install flask
sudo pip3 install flask_wtf
sudo pip3 install flask-sqlalchemy
#sudo pip3 install sqlalchemy

echo "Creating TACACSGUI folder"
sudo mkdir -p /opt/tacacsgui
sudo chown www-data:www-data -R /opt/tacacsgui

echo "Would you like to reset the database TACACSGUI? (Y/N)"
read answer
if [[ "$answer" == "Y" || "$answer" == "y" ]]
then
	mysql -uroot -pNigAfDov < ../database/schema.sql
fi

sudo rsync -rv ../app ../run.py ../config.py ../deployment/synchronizer.sh /opt/tacacsgui/
sudo chown www-data:www-data -R /opt/tacacsgui
sudo rsync -rv ../systemd/tacacsgui.service /etc/systemd/system/
sudo systemctl enable tacacsgui
sudo systemctl start tacacsgui
echo "* * * * *	root	/bin/bash /opt/synchronizer.sh" >> /etc/crontab
#sudo crontab -e
sudo service cron reload
