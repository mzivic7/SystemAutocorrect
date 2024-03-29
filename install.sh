#!/bin/bash
sudo cp autocorrect.py /usr/local/sbin/autocorrect
sudo cp autocorrect.service /etc/systemd/system/autocorrect.service
sudo chmod 755 /usr/local/sbin/autocorrect
sudo chmod 644 /etc/systemd/system/autocorrect.service
sudo mkdir /etc/autocorrect/
sudo cp config.ini /etc/autocorrect/config.ini
sudo cp -r keymaps /etc/autocorrect/
sudo cp -r custom /etc/autocorrect/
sudo chown root:root /etc/systemd/system/autocorrect.service /usr/local/sbin/autocorrect
sudo systemctl enable autocorrect.service
sudo systemctl start autocorrect.service
echo "Autocorrect service is enabled and started." 

